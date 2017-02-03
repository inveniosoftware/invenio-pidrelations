# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
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

"""API for PID relations concepts."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_db import db
from .models import PIDRelation, RelationType
from .api import PIDConcept
from flask import current_app


class PIDVersioning(PIDConcept):
    """API for PID versioning relations.

    - Adds automatic redirection handling for Parent-LastChild
    - Sets stricter method signatures, e.g.: 'index' is mandatory parameter
        when calling 'insert'.
    """

    def __init__(self, pid=None, child=None, parent=None, relation=None):
        VERSION_TYPE = \
            current_app.config['PIDRELATIONS_RELATION_TYPES']['VERSION']
        self.relation_type = VERSION_TYPE
        if relation is not None:
            assert relation.relation_type == VERSION_TYPE
            return super(PIDVersioning, self).__init__(relation=relation)
        if pid:
            pass
            # determine whether it's the child or parent (if both, raise)
            # if child:
            #   self.child = pid
            #   self.parent = PIDConcept.get_parent(
            #       pid, relation_type=self.relation_type)
            # if parent:
            #   self.parent = pid
            #   self.child = None
            super(PIDVersioning, self).__init__(
                child=child, parent=parent, relation_type='VERSION',
                relation=relation)
        else:
            self.child = child
            self.parent = parent
        self.parent = PIDConcept.get_parent(pid)

    def insert(self, child, index):
        # Impose index as mandatory key
        # TODO: For linking usecase: check if 'pid' has a parent already,
        #       if so, raise or remove it first
        assert index is not None, "You must specify the insertion index."
        with db.session.begin_nested():
            super(PIDVersioning, self).insert(child, index=index)
            self.parent.redirect(child)

    def remove(self):
        # Impose index as mandatory key
        # TODO: When removing single versioned element remove the redirection
        # always reorders after removing
        with db.session.begin_nested():
            return super(PIDVersioning).remove(reorder=True)
            last_child = self.get_last_child()
            self.parent.redirect(last_child)

    def create_relation(self, order):
        assert order is not None, "Relation cannot be unordered"
        super(PIDVersioning, self).create_relation(order=order)

    def create_parent(self, parent_pid_value):
        relation = super(PIDVersioning, self).create_parent(parent_pid_value)
        self.parent.redirect(self.child)  # TODO: Move to PIDVersioning API
        return relation


__all__ = (
    'PIDVersioning',
)
