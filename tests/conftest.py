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

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from elasticsearch.exceptions import RequestError
from flask import Flask
from flask_babelex import Babel
from invenio_db import db as db_
from invenio_db import InvenioDB
from invenio_indexer import InvenioIndexer
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records import InvenioRecords, Record
from invenio_search import InvenioSearch, current_search, current_search_client
from marshmallow import fields
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_pidrelations import InvenioPIDRelations
from invenio_pidrelations.config import RelationType
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.serializers.schemas import RelationSchema
from invenio_pidrelations.utils import resolve_relation_type_config


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
    )
    InvenioPIDStore(app_)
    InvenioDB(app_)
    InvenioPIDRelations(app_)
    InvenioRecords(app_)
    InvenioIndexer(app_)
    InvenioSearch(app_)
    Babel(app_)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def es(app):
    """Provide elasticsearch access."""
    try:
        list(current_search.create())
    except RequestError:
        list(current_search.delete(ignore=[400, 404]))
        list(current_search.create())
    current_search_client.indices.refresh()
    yield current_search_client
    list(current_search.delete(ignore=[404]))


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if database_exists(str(db_.engine.url)):
        db_.session.remove()
        drop_database(str(db_.engine.url))
    create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    drop_database(db_.engine.url)
    # Dispose the engine in order to close all connections. This is
    # needed for sqlite in memory databases.
    db_.engine.dispose()


@pytest.fixture()
def pids(app, db):
    """Test PIDs fixture."""
    # TODO: Head PIDs do not have redirects as they are created outside API
    h1 = PersistentIdentifier.create('recid', 'foobar', object_type='rec',
                                     status=PIDStatus.REGISTERED)
    h1v1 = PersistentIdentifier.create('recid', 'foobar.v1', object_type='rec')
    h1v2 = PersistentIdentifier.create('recid', 'foobar.v2', object_type='rec')
    h1v3 = PersistentIdentifier.create('recid', 'foobar.v3', object_type='rec')

    ORDERED = resolve_relation_type_config('ordered').id
    UNORDERED = resolve_relation_type_config('unordered').id
    PIDRelation.create(h1, h1v1, ORDERED, 0)
    PIDRelation.create(h1, h1v2, ORDERED, 1)
    PIDRelation.create(h1, h1v3, ORDERED, 2)
    h1.redirect(h1v3)

    h2 = PersistentIdentifier.create('recid', 'spam', object_type='rec',
                                     status=PIDStatus.REGISTERED)
    h2v1 = PersistentIdentifier.create('recid', 'spam.v1')
    PIDRelation.create(h2, h2v1, ORDERED, 0)
    h2.redirect(h2v1)

    c1 = PersistentIdentifier.create('recid', 'bazbar')
    c1r1 = PersistentIdentifier.create('recid', 'resource1')
    c1r2 = PersistentIdentifier.create('recid', 'resource2')

    pid1 = PersistentIdentifier.create('recid', 'eggs')
    PIDRelation.create(c1, c1r1, UNORDERED, None)
    PIDRelation.create(c1, c1r2, UNORDERED, None)
    return {
        'h1': h1,
        'h1v1': h1v1,
        'h1v2': h1v2,
        'h1v3': h1v3,
        'h2': h2,
        'h2v1': h2v1,
        'c1': c1,
        'c1r1': c1r1,
        'c1r2': c1r2,
        'pid1': pid1,
    }


@pytest.fixture()
def nested_pids_and_relations(app, db):
    """Fixture for a nested PIDs and the expected serialized relations."""
    # Create some PIDs and connect them into different nested PID relations
    pids = {}
    for idx in range(1, 12):
        pid_value = str(idx)
        p = PersistentIdentifier.create('recid', pid_value, object_type='rec',
                                        status=PIDStatus.REGISTERED)
        pids[idx] = p

    ORDERED = resolve_relation_type_config('ordered').id
    UNORDERED = resolve_relation_type_config('unordered').id
    VERSION = resolve_relation_type_config('version').id

    #    1  (Version)
    #  / | \
    # 2  3 4
    PIDRelation.create(pids[1], pids[2], VERSION, 0)
    PIDRelation.create(pids[1], pids[3], VERSION, 1)
    PIDRelation.create(pids[1], pids[4], VERSION, 2)

    #    5  (Ordered)
    #  / | \
    # 6  4 7
    PIDRelation.create(pids[5], pids[6], ORDERED, 0)
    PIDRelation.create(pids[5], pids[4], ORDERED, 1)
    PIDRelation.create(pids[5], pids[7], ORDERED, 2)

    #    4  (Ordered)
    #  / |
    # 8  9
    PIDRelation.create(pids[4], pids[8], ORDERED, 0)
    PIDRelation.create(pids[4], pids[9], ORDERED, 1)

    #   10  (Unordered)
    #  / |
    # 4  11
    PIDRelation.create(pids[10], pids[4], UNORDERED, None)
    PIDRelation.create(pids[10], pids[11], UNORDERED, None)

    # Define the expected PID relation tree for of the PIDs
    expected_relations = {}
    expected_relations[4] = {
        'relations': {
            'version': [
                {
                    'children': [{'pid_type': 'recid', 'pid_value': '2'},
                                 {'pid_type': 'recid', 'pid_value': '3'},
                                 {'pid_type': 'recid', 'pid_value': '4'}],
                    'is_child': True,
                    'index': 2,
                    'previous': {'pid_type': 'recid', 'pid_value': '3'},
                    'next': None,
                    'is_last': True,
                    'is_ordered': True,
                    'is_parent': False,
                    'parent': {'pid_type': 'recid', 'pid_value': '1'},
                    'type': 'version'
                }
            ],
            'ordered': [
                {
                    'children': [{'pid_type': 'recid', 'pid_value': '6'},
                                 {'pid_type': 'recid', 'pid_value': '4'},
                                 {'pid_type': 'recid', 'pid_value': '7'}],
                    'is_child': True,
                    'index': 1,
                    'previous': {'pid_type': 'recid', 'pid_value': '6'},
                    'next': {'pid_type': 'recid', 'pid_value': '7'},
                    'is_last': False,
                    'is_ordered': True,
                    'is_parent': False,
                    'parent': {'pid_type': 'recid', 'pid_value': '5'},
                    'type': 'ordered'
                },
                {
                    'children': [{'pid_type': 'recid', 'pid_value': '8'},
                                 {'pid_type': 'recid', 'pid_value': '9'}],
                    'is_child': False,
                    'index': None,
                    'previous': None,
                    'next': None,
                    'is_last': None,
                    'is_ordered': True,
                    'is_parent': True,
                    'parent': {'pid_type': 'recid', 'pid_value': '4'},
                    'type': 'ordered'
                }
            ],
            'unordered': [
                {
                    'children': [{'pid_type': 'recid', 'pid_value': '4'},
                                 {'pid_type': 'recid', 'pid_value': '11'}],
                    'is_child': True,
                    'index': None,
                    'previous': None,
                    'next': None,
                    'is_last': False,
                    'is_ordered': True,
                    'is_parent': False,
                    'parent': {'pid_type': 'recid', 'pid_value': '10'},
                    'type': 'unordered'
                },
            ]
        }
    }
    return pids, expected_relations


class CustomRelationSchema(RelationSchema):
    """PID relation Schema containing only children and one extra field."""

    class Meta:
        """Meta fields of the schema."""

        fields = ("children", "has_three_children", )

    has_three_children = fields.Method('dump_has_three_children')

    def dump_has_three_children(self, obj):
        """Dump information if relation has exactly three children."""
        return obj.children.count() == 3


@pytest.yield_fixture()
def custom_relation_schema(app):
    """Fixture for PID relations config with custom schemas."""
    orig = app.config['PIDRELATIONS_RELATION_TYPES']
    app.config['PIDRELATIONS_RELATION_TYPES'] = [
        RelationType(0, 'ordered', 'Ordered',
                     'invenio_pidrelations.api:PIDConceptOrdered',
                     CustomRelationSchema),
        RelationType(1, 'unordered', 'Unordered',
                     'invenio_pidrelations.api:PIDConcept',
                     CustomRelationSchema),
        RelationType(2, 'version', 'Version',
                     'invenio_pidrelations.contrib.versioning:PIDVersioning',
                     CustomRelationSchema),
    ]
    yield app
    app.config['PIDRELATIONS_RELATION_TYPES'] = orig


@pytest.fixture()
def version_pids(app, db):
    """Versioned PIDs fixture with one parent and two versions."""
    h1 = PersistentIdentifier.create('recid', 'foobar', object_type='rec',
                                     status=PIDStatus.REGISTERED)
    h1v1 = PersistentIdentifier.create('recid', 'foobar.v1', object_type='rec',
                                       status=PIDStatus.REGISTERED)
    h1v2 = PersistentIdentifier.create('recid', 'foobar.v2', object_type='rec',
                                       status=PIDStatus.REGISTERED)
    pv = PIDVersioning(parent=h1)
    pv.insert_child(h1v1)
    pv.insert_child(h1v2)
    db.session.commit()
    return {
        'h1': h1,
        'h1v1': h1v1,
        'h1v2': h1v2,
    }


@pytest.fixture()
def records(pids, db):
    """Fixture for the records."""
    pid_versions = ['h1v1', 'h1v2', 'h2v1']
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
        },
    }
    data = {
        name: {'title': 'Test version {}'.format(name),
               'recid': pids[name].pid_value,
               '$schema': schema}
        for name in pid_versions
    }
    records = dict()
    for name in pid_versions:
        record = Record.create(data[name])
        pids[name].assign('rec', record.id)
        records[name] = record
    return records


@pytest.fixture()
def indexed_records(es, records):
    """Fixture for the records, which are already indexed."""
    # es.indices.flush('*')
    # # delete all elasticsearch indices and recreate them
    # for deleted in current_search.delete(ignore=[404]):
    #     pass
    # for created in current_search.create(None):
    #     pass
    # flush the indices so that indexed records are searchable
    for pid_name, record in records.items():
        RecordIndexer().index(record)
    es.indices.flush('*')
    return records
