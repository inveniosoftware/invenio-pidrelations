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

"""Schema tests."""

from marshmallow import Schema

from invenio_pidrelations.serializers.schemas import RelationSchema, PIDRelationsMixin
from invenio_pidrelations.models import PIDRelation


class SampleRecordSchema(Schema, PIDRelationsMixin):
    """Sample record schema."""
    pass


def test_schema(app, nested_pids_and_relations):
    """Test the marshmallow schema serialization."""
    schema = MyRecordSchema(strict=True)

    pids, exp_relations = nested_pids_and_relations
    for p_idx in exp_relations.keys():
        pid = pids[p_idx]
        expected = exp_relations[p_idx]
        input_data = {'pid': pid}
        schema.context['pid'] = pid
        data, errors = schema.dump(input_data)
        assert not errors
        assert expected == data  # Test against hand-crafted fixture
    pass


def test_custom_schema(app, nested_pids_and_relations, custom_relation_schema):
    """Test the marshmallow schema serialization with custom schema."""
    schema = MyRecordSchema(strict=True)
    pids, exp_relations = nested_pids_and_relations

    pid = pids[4]
    input_data = {'pid': pid}
    schema.context['pid'] = pid
    data, errors = schema.dump(input_data)
    expected = {
        'relations': {
            'version': [
                {
                    'children': [{'pid_type': 'recid', 'pid_value': '2'},
                                 {'pid_type': 'recid', 'pid_value': '3'},
                                 {'pid_type': 'recid', 'pid_value': '4'}],
                    'has_three_children': True,
                },
            ],
            'ordered': [
                {
                    'children': [{'pid_type': 'recid', 'pid_value': '6'},
                                 {'pid_type': 'recid', 'pid_value': '4'},
                                 {'pid_type': 'recid', 'pid_value': '7'}],
                    'has_three_children': True,
                },
                {
                    'children': [{'pid_type': 'recid', 'pid_value': '8'},
                                 {'pid_type': 'recid', 'pid_value': '9'}],
                    'has_three_children': False,
                },
            ],
            'unordered': [
                {
                    'children': [{'pid_type': 'recid', 'pid_value': '4'},
                                 {'pid_type': 'recid', 'pid_value': '11'}],
                    'has_three_children': False,
                },
            ],
        }
    }
    assert not errors
    assert expected == data
