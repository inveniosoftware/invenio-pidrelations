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

from invenio_pidstore.models import PersistentIdentifier

from invenio_pidrelations.models import PIDRelation, RelationType


def test_pidrelation(app, db):
    """Test version import."""
    pid = PersistentIdentifier.create('doi', 'foobar.v1')
    head_pid, pid_relation = PIDRelation.create_head_pid(pid, 'foobar')
    db.session.commit()

    assert head_pid.pid_value == 'foobar'
    assert head_pid.pid_type == pid.pid_type


def test_foo(app, db):
    h1 = PersistentIdentifier.create('doi', 'foobar')
    h1v1 = PersistentIdentifier.create('doi', 'foobar.v1')
    h1v2 = PersistentIdentifier.create('doi', 'foobar.v2')
    PIDRelation.create(h1, h1v1, RelationType.VERSION, 0)
    PIDRelation.create(h1, h1v2, RelationType.VERSION, 1)

    h2 = PersistentIdentifier.create('doi', 'spam')
    h2v1 = PersistentIdentifier.create('doi', 'spam.v1')
    PIDRelation.create(h2, h2v1, RelationType.VERSION, 0)

    c1 = PersistentIdentifier.create('doi', 'bazbar')
    c1r1 = PersistentIdentifier.create('doi', '12345')
    c1r2 = PersistentIdentifier.create('doi', '54321')

    pid1 = PersistentIdentifier.create('doi', 'other')
    PIDRelation.create(c1, c1r1, RelationType.COLLECTION, None)
    PIDRelation.create(c1, c1r2, RelationType.COLLECTION, None)
    assert PIDRelation.is_head_pid(h1)
    assert not PIDRelation.is_head_pid(h1v1)
    assert not PIDRelation.is_head_pid(h1v2)
    assert PIDRelation.is_head_pid(h2)
    assert not PIDRelation.is_head_pid(h2v1)
    assert not PIDRelation.is_head_pid(c1)
    assert not PIDRelation.is_head_pid(c1r1)
    assert not PIDRelation.is_head_pid(c1r2)
    assert not PIDRelation.is_head_pid(pid1)

    assert PIDRelation.get_head_pid(h1) == h1
    assert PIDRelation.get_head_pid(h1v1) == h1
    assert PIDRelation.get_head_pid(h1v2) == h1
    assert PIDRelation.get_head_pid(h2) == h2
    assert PIDRelation.get_head_pid(h2v1) == h2
    assert PIDRelation.get_head_pid(h2v1) == h2
    assert PIDRelation.get_head_pid(pid1) is None
    assert PIDRelation.get_head_pid(c1) is None
    assert PIDRelation.get_head_pid(c1r1) is None


def test_head_pid_methods(app, db):
    """Test Head PID methods."""

    # Create an orphan PID
    pid = PersistentIdentifier.create('doi', 'foobar.v1')
    db.session.commit()

    assert not PIDRelation.is_head_pid(pid)
    assert PIDRelation.get_head_pid(pid) is None

    # Add a Head PID to the orphan PID
    head_pid, pid_relation = PIDRelation.create_head_pid(pid, 'foobar')
    db.session.commit()

    assert PIDRelation.is_head_pid(head_pid)
    assert not PIDRelation.is_head_pid(pid)
    assert PIDRelation.get_head_pid(head_pid) == head_pid
    assert PIDRelation.get_head_pid(pid) == head_pid


def test_version_pid_methods(app, db):
    pid = PersistentIdentifier.create('doi', 'foobar.v1')
    assert PIDRelation.is_version_pid(pid)
    assert PIDRelation.is_latest_pid(pid)

    head_pid, pid_relation = PIDRelation.create_head_pid(pid, 'foobar')
    db.session.commit()

    assert not PIDRelation.is_head_pid(pid)

    assert PIDRelation.get_head_pid(head_pid) == head_pid
    assert PIDRelation.get_head_pid(pid) == head_pid
