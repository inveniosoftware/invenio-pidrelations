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

from copy import deepcopy

from invenio_indexer.signals import before_record_index
from werkzeug.utils import cached_property

from invenio_pidrelations import config
from invenio_pidrelations.indexers import index_relations
from invenio_pidrelations.utils import obj_or_import_string


class _InvenioPIDRelationsState(object):
    """InvenioPIDRelations REST state."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app

    @cached_property
    def relation_types(self):
        return self.app.config.get('PIDRELATIONS_RELATION_TYPES', {})


class InvenioPIDRelations(object):
    """Invenio-PIDRelations extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['invenio-pidrelations'] = _InvenioPIDRelationsState(app)

        # # Register indexers the default indexer if necessary
        # if app.config.get('PIDRELATIONS_REGISTER_DEFAULT_INDEXER'):
        #     before_record_index.connect(index_relations, sender=app)

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('PIDRELATIONS_'):
                app.config.setdefault(k, getattr(config, k))
