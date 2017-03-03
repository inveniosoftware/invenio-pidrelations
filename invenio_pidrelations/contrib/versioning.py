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

from flask import current_app
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from ..api import PIDConceptOrdered
from ..models import PIDRelation
from ..utils import resolve_relation_type_config


class PIDVersioning(PIDConceptOrdered):
    """API for PID versioning relations.

    - Adds automatic redirection handling for Parent-LastChild
    - Sets stricter method signatures, e.g.: 'index' is mandatory parameter
        when calling 'insert'.
    """

    def __init__(self, child=None, parent=None, relation=None):
        """Create a PID versioning API."""
        self.relation_type = resolve_relation_type_config('version').id
        if relation is not None:
            if relation.relation_type != self.relation_type:
                raise ValueError("Provided PID relation ({0}) is not a "
                                 "version relation.".format(relation))
            super(PIDVersioning, self).__init__(relation=relation)
        else:
            return super(PIDVersioning, self).__init__(
                child=child, parent=parent, relation_type=self.relation_type,
                relation=relation)
        if self.child:
            self.relation = PIDRelation.query.filter(
                PIDRelation.child_id == self.child.id,
                PIDRelation.parent_id == self.parent.id,
                PIDRelation.relation_type == self.relation_type,
            ).one_or_none()

    def insert_child(self, child, index=-1):
        """Insert child into versioning scheme.

        Parameter 'index' is has to be an integer.
        """
        # Impose index as mandatory key
        # TODO: For linking usecase: check if 'pid' has a parent already,
        #       if so, raise or remove it first
        if index is None:
            raise ValueError(
                "Incorrect value for child index: {0}".format(index))

        with db.session.begin_nested():
            super(PIDVersioning, self).insert_child(child, index=index)
            self.parent.redirect(child)

    def remove_child(self, child):
        """Remove a child from a versioning scheme.

        Extends the base method call with always reordering after removal and
        adding a redirection from the parent to the last child.
        """
        # TODO: Add support for removing a single child
        if self.children.count() == 1:
            raise Exception("Removing single child is not supported.")
        with db.session.begin_nested():
            super(PIDVersioning, self).remove_child(child, reorder=True)
            self.parent.redirect(self.last_child)

    def create_parent(self, pid_value, status=PIDStatus.REGISTERED,
                      redirect=True):
        """Create a parent PID from a child and create a new PID versioning."""
        if self.has_parents:
            raise Exception("Parent already exists for this child.")
        self.parent = PersistentIdentifier.create(
            self.child.pid_type, pid_value,
            object_type=self.child.object_type,
            status=status)
        self.relation = PIDRelation.create(
            self.parent, self.child, self.relation_type, 0)
        if redirect:
            self.parent.redirect(self.child)

    # TODO: This will be required for finding the last draft
    # def get_last_child(self, status=PIDStatus.REGISTERED):
    #     pass


versioning_blueprint = Blueprint(
    'invenio_pidrelations.versioning',
    __name__,
    template_folder='templates'
)


@versioning_blueprint.app_template_filter()
def latest_pid_version(pid):
    """Get last PID."""
    return (PIDVersioning(child=pid).children
            .filter(PersistentIdentifier.status == PIDStatus.REGISTERED)
            .last())


@versioning_blueprint.app_template_filter()
def head_pid_version(pid):
    """Get head PID of a PID."""
    return PIDVersioning.get_parent(pid)


@versioning_blueprint.app_template_test()
def latest_version(pid):
    """Determine if PID is the last version."""
    return PIDVersioning.is_latest(pid)


@versioning_blueprint.app_template_filter()
def all_versions(pid):
    """Get all versions of a PID."""
    return PIDVersioning(pid).children()


__all__ = (
    'PIDVersioning',
    'versioning_blueprint'
)
