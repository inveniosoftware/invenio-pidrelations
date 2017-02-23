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

"""Minimal Flask application example.

First install Invenio-PIDRelations, setup the application and load
fixture data by running:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Next, start the development server:

.. code-block:: console

   $ export FLASK_APP=app.py FLASK_DEBUG=1
   $ flask run

and open the example application in your browser:

.. code-block:: console

    $ open http://127.0.0.1:5000/

To reset the example application run:

.. code-block:: console

    $ ./app-teardown.sh
"""

from __future__ import absolute_import, print_function

from flask import Flask, redirect, render_template, request, url_for
from flask_babelex import Babel
from invenio_db import InvenioDB, db
from invenio_indexer import InvenioIndexer
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_pidstore.resolver import Resolver
from invenio_records import InvenioRecords
from invenio_records.api import Record
from marshmallow import Schema, fields

from invenio_pidrelations import InvenioPIDRelations
from invenio_pidrelations.contrib.records import versioned_minter
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.serializers.schemas import PIDRelationsMixin, \
    RelationsSchema
from invenio_pidrelations.views import blueprint as pidrelations_blueprint

# Create Flask application
app = Flask(__name__, template_folder='.')
app.config['TEMPLATES_AUTO_RELOAD'] = True

InvenioDB(app)
InvenioPIDStore(app)
InvenioPIDRelations(app)
app.register_blueprint(pidrelations_blueprint)
InvenioIndexer(app)
InvenioRecords(app)

record_resolver = Resolver(
    pid_type='recid', object_type='rec', getter=Record.get_record
)


class SimpleRecordSchema(Schema, PIDRelationsMixin):
    """Tiny schema for our simple record."""

    recid = fields.Str()
    title = fields.Str()
    body = fields.Str()


@app.route('/')
def index():
    heads = PIDVersioning.parents
    return render_template('index.html', heads=heads)


@app.route('/create', methods=['POST'])
def create():
    create_simple_record(request.form)
    return redirect(url_for('index'))


@app.template_filter()
def to_record(pid):
    return SimpleRecordSchema().dump(record_resolver.resolve(pid.pid_value)[1])


def create_simple_record(data):

    # Create the record and mint a PID
    data, errors = SimpleRecordSchema().load(data)
    parent = data.get('parent')
    if parent != 'new':
        data['_relations'] = {'version': {'parent': parent}}
    rec = Record.create(data)
    rec.commit()

    # The `invenio_pidrelations.contrib.records.versioned_minter` will take
    # care of creating the necessary PIDRelation entries.
    record_minter(rec.id, rec)
    db.session.commit()


@versioned_minter(pid_type='recid')
def record_minter(record_uuid, data):
    provider = RecordIdProvider.create('rec', record_uuid)
    data['recid'] = provider.pid.pid_value
    return provider.pid
