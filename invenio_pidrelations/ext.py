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

"""Invenio module that adds PID relations to the Invenio-PIDStore module."""

from __future__ import absolute_import, print_function

from werkzeug.utils import cached_property

from . import config
from .indexers import index_relations


class _InvenioPIDRelationsState(object):
    """InvenioPIDRelations REST state."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app

    @cached_property
    def relation_types(self):
        return self.app.config.get('PIDRELATIONS_RELATION_TYPES', {})

    @cached_property
    def primary_pid_type(self):
        return self.app.config.get('PIDRELATIONS_PRIMARY_PID_TYPE')

    def indexed_relations(self):
        """Load the configuration for indexed relations."""
        indexed = self.app.config.get('PIDRELATIONS_INDEXED_RELATIONS')
        if not indexed:
            return {}
        result = deepcopy(indexed)
        for pid_value, conf in result.items():
            conf.update(dict(api=obj_or_import_string(conf['api'])))
        return result


class InvenioPIDRelations(object):
    """Invenio-PIDRelations extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        # app.register_blueprint(blueprint)
        app.extensions['invenio-pidrelations'] = _InvenioPIDRelationsState(app)

        # Register indexers if they are required
        if app.config.get('PIDRELATIONS_INDEX_RELATIONS'):
            from invenio_indexer.signals import before_record_index
            before_record_index.connect(index_relations, sender=app)

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('PIDRELATIONS_'):
                app.config.setdefault(k, getattr(config, k))
