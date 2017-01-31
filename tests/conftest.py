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

import shutil
import os
import tempfile

import six
import pytest
from flask import Flask
from flask_babelex import Babel
from invenio_db import InvenioDB, db as db_
from invenio_indexer import InvenioIndexer
from invenio_records import InvenioRecords, Record
from invenio_search import InvenioSearch, current_search, current_search_client
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.fetchers import recid_fetcher
from invenio_indexer.api import RecordIndexer

from invenio_pidrelations import InvenioPIDRelations

from sqlalchemy_utils.functions import create_database, database_exists
from invenio_pidrelations.models import PIDRelation, RelationType
from invenio_pidstore.models import PersistentIdentifier, PIDStatus


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
        PIDRELATIONS_DEFAULT_PID_FETCHER = 'recid',
    )
    InvenioPIDStore(app_)
    InvenioPIDRelations(app_)
    InvenioDB(app_)
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
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture()
def pids(db):
    """Test PIDs fixture."""
    # TODO: Head PIDs do not have redirects as they are created outside API
    h1 = PersistentIdentifier.create('doi', 'foobar', object_type='rec',
                                     status=PIDStatus.REGISTERED)
    h1v1 = PersistentIdentifier.create('doi', 'foobar.v1', object_type='rec')
    h1v2 = PersistentIdentifier.create('doi', 'foobar.v2', object_type='rec')
    PIDRelation.create(h1, h1v2, RelationType.VERSION, 1)
    PIDRelation.create(h1, h1v1, RelationType.VERSION, 0)
    h1.redirect(h1v2)

    h2 = PersistentIdentifier.create('doi', 'spam', object_type='rec',
                                     status=PIDStatus.REGISTERED)
    h2v1 = PersistentIdentifier.create('doi', 'spam.v1')
    PIDRelation.create(h2, h2v1, RelationType.VERSION, 0)
    h2.redirect(h2v1)

    c1 = PersistentIdentifier.create('doi', 'bazbar')
    c1r1 = PersistentIdentifier.create('doi', 'resource1')
    c1r2 = PersistentIdentifier.create('doi', 'resource2')

    pid1 = PersistentIdentifier.create('doi', 'eggs')
    PIDRelation.create(c1, c1r1, RelationType.COLLECTION, None)
    PIDRelation.create(c1, c1r2, RelationType.COLLECTION, None)
    return {
        'h1': h1,
        'h1v1': h1v1,
        'h1v2': h1v2,
        'h2': h2,
        'h2v1': h2v1,
        'c1': c1,
        'c1r1': c1r1,
        'c1r2': c1r2,
        'pid1': pid1,
    }


@pytest.fixture()
def records(pids, db):
    pid_versions = ['h1v1', 'h1v2', 'h2v1']
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
        },
    }
    data = {
        name: {'title': 'Test version {}'.format(name),
               'control_number': pids[name].pid_value,
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
def indexed_records(records):
    current_search_client.indices.flush('*')
    # delete all elasticsearch indices and recreate them
    for deleted in current_search.delete(ignore=[404]):
        pass
    for created in current_search.create(None):
        pass
    # flush the indices so that indexed records are searchable
    for pid_name, record in records.items():
        RecordIndexer().index(record)
    current_search_client.indices.flush('*')
    return records
