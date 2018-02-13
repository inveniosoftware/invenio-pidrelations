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

"""Indexer tests."""

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_records.api import Record
from test_helpers import compare_dictionaries

from invenio_pidrelations.contrib.versioning import PIDNodeVersioning
from invenio_pidrelations.indexers import index_relations


def test_index_relations(app, db):
    """Test the index_relations method."""

    data_v1 = {'body': u'test_body',
               'title': u'test_title'}
    data_v2 = {'body': u'test_body2',
               'title': u'test_title2'}

    # add first child to the relation
    rec_v1 = Record.create(data_v1)
    parent_pid = RecordIdProvider.create(object_type='rec',
                                         object_uuid=None,
                                         status=PIDStatus.REGISTERED).pid
    data_v1['conceptrecid'] = parent_pid.pid_value
    provider = RecordIdProvider.create('rec', rec_v1.id)
    data_v1['recid'] = provider.pid.pid_value
    versioning = PIDNodeVersioning(pid=parent_pid)
    versioning.insert_child(child=provider.pid)
    db.session.commit()
    output = index_relations(app, 'recid', record=rec_v1)
    expected_output = \
        {'relations': {
            'version': [{
                u'children': [{u'pid_type': u'recid',
                               u'pid_value': u'2'}],
                u'index': 0,
                u'is_child': True,
                u'is_last': True,
                u'is_parent': False,
                u'next': None,
                u'parent': {u'pid_type': u'recid',
                            u'pid_value': u'1'},
                u'previous': None,
                u'type': 'version'}]}}
    assert compare_dictionaries(output, expected_output)
    # add second child to the relation
    rec_v2 = Record.create(data_v2)
    data_v2['conceptrecid'] = parent_pid.pid_value
    provider_v2 = RecordIdProvider.create('rec', rec_v2.id)
    versioning.insert_child(child=provider_v2.pid)
    db.session.commit()
    output = index_relations(app, 'recid', record=rec_v2)
    expected_output = \
        {'relations': {
            'version': [{
                u'children': [{u'pid_type': u'recid',
                               u'pid_value': u'2'},
                              {u'pid_type': u'recid',
                               u'pid_value': u'3'}],
                u'index': 1,
                u'is_child': True,
                u'is_last': True,
                u'is_parent': False,
                u'next': None,
                u'parent': {u'pid_type': u'recid',
                            u'pid_value': u'1'},
                u'previous': {u'pid_type': u'recid',
                              u'pid_value': u'2'},
                u'type': 'version'}]}}
    assert compare_dictionaries(output, expected_output)
