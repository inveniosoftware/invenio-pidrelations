# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Module tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.utils import resolve_relation_type_config


def test_api(app, db):
    from invenio_pidstore.providers.recordid import RecordIdProvider
    def create_pid(value):
        return PersistentIdentifier.create(
            'recid', value, object_type='rec', status=PIDStatus.REGISTERED)
    parent_pid = create_pid(0)
    versioning = PIDVersioning(parent=parent_pid)
    for pid_value in range(1, 10):
        version_pid = create_pid(pid_value)
        versioning.insert_child(child=version_pid)

    pvers = PIDVersioning(parent=parent_pid)
    cvers = PIDVersioning(child=version_pid)
    rvers = PIDVersioning(child=version_pid, parent=parent_pid)

    import ipdb
    ipdb.set_trace()

def test_version_pids_create(app, db):

    # Create a child, initialize the Versioning API and create a parent
    assert PersistentIdentifier.query.count() == 0
    # Create a child
    h1v1 = PersistentIdentifier.create('recid', '12345', object_type='rec',
                                       status=PIDStatus.REGISTERED)
    assert PersistentIdentifier.query.count() == 1
    pv = PIDVersioning(child=h1v1)
    # Create a parent
    pv.create_parent('12345.parent')
    assert PersistentIdentifier.query.count() == 2
    assert pv.parent.get_redirect() == h1v1
    assert pv.parent.status == PIDStatus.REDIRECTED
    # Make sure 'pid_type', 'object_type' and 'status' are inherited from child
    assert pv.parent.pid_type == pv.child.pid_type
    assert pv.parent.object_type == pv.child.object_type

    pr = PIDRelation.query.one()
    assert pr.child == h1v1
    assert pr.parent == pv.parent

    VERSION = resolve_relation_type_config('version').id
    assert pr.relation_type == VERSION
    assert pr.index == 0


def test_version_api_edit(app, db, version_pids):
    h1, h1v1, h1v2 = (version_pids[p] for p in ['h1', 'h1v1', 'h1v2'])
    pv = PIDVersioning(parent=h1)

    assert [h1v1, h1v2] == pv.children.all()
    assert h1.get_redirect() == h1v2
    assert pv.last_child == h1v2

    h1v3 = PersistentIdentifier.create('recid', 'foobar.v3', object_type='rec',
                                       status=PIDStatus.REGISTERED)
    pv.insert_child(h1v3)
    assert [h1v1, h1v2, h1v3] == pv.children.all()
    assert h1.get_redirect() == h1v3
    pv.last_child == h1v3

    pv.remove_child(h1v3)
    assert h1.get_redirect() == h1v2
    assert pv.last_child == h1v2

    pv.remove_child(h1v2)
    assert h1.get_redirect() == h1v1
    assert pv.last_child == h1v1
