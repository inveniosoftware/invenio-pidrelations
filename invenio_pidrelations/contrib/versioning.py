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

from flask import current_app, Blueprint
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from ..api import PIDConceptOrdered
from ..models import PIDRelation
from ..utils import resolve_relation_type_config


class PIDVersioning(PIDConceptOrdered):
    """API for PID versioning relations.

    - Adds automatic redirection handling for Parent-LastChild
    """

    @classmethod
    def get(cls, child=None, relation=None):
        """Retrieve a PIDConcept.

        One of those parameters must be provided: parent or child or relation.

        :param child: child PID.
        :param relation: relation which is part of this PIDConcept. It's
            parent PID and relation_type will be used. Ignored if child is
            given.
        :type relation: :py:class:`.models.PIDRelation`

        :returns: a PIDVersioning or None if no version relation is linked
            to the child PIDs.
        """
        if child:
            # TODO: retrieve the single possible version relation linking
            # the child PID
            pass
        else:
            return PIDConceptOrdered.get(relation=relation)

    def add_child(self, child, index=-1):
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
            if self.last_child is not None:
                self.parent.redirect(self.last_child)
            # else:
            #     self.parent.unassign()
            #     self.parent.delete()  # TODO: Deleting redirection

    # def create_parent(self, pid_value, status=PIDStatus.REGISTERED,
    #                   redirect=True):
    #     """Create a parent PID from a child and create a new PID versioning."""
    #     if self.has_parents:
    #         raise Exception("Parent already exists for this child.")
    #     self.parent = PersistentIdentifier.create(
    #         self.child.pid_type, pid_value,
    #         object_type=self.child.object_type,
    #         status=status)
    #     self.relation = PIDRelation.create(
    #         self.parent, self.child, self.relation_type, 0)
    #     if redirect:
    #         self.parent.redirect(self.child)


    @property
    def draft_child(self):
        """Get the last non-registered child"""
        return self.get_children(ordered=False).filter(
                PIDRelation.index.isnot(None),
                PersistentIdentifier.status == PIDStatus.RESERVED).order_by(
                    PIDRelation.index.desc()).one_or_none()

    @property
    def draft_child_deposit(self):
        """Get the deposit of the draft child.

        Return `None` if no new-version deposit exists."""
        from invenio_pidrelations.contrib.records import RecordDraft
        if self.draft_child:
            return RecordDraft.get_draft(self.draft_child)
        else:
            return None

    def add_draft_child(self, child):
        if not self.draft_child:
            # FIXME: reimplement without using children
            pass
            # with db.session.begin_nested():
            #     super(PIDVersioning, self).insert_child(child, index=-1)
        else:
            raise Exception(
                "Draft child already exists for this relation: {0}".format(
                    self.draft_child))

    def remove_draft_child(self):
        if self.draft_child:
            # FIXME: reimplement without using children
            pass
            # with db.session.begin_nested():
            #     super(PIDVersioning, self).remove_child(self.draft_child,
            #                                             reorder=True)

    def update_redirect(self):
        if self.last_child:
            if self.parent.status == PIDStatus.RESERVED:
                self.parent.register()
            self.parent.redirect(self.last_child)

    @property
    def children(self):
        """Children of the parent."""
        return self.get_children(pid_status=PIDStatus.REGISTERED, ordered=True)


versioning_blueprint = Blueprint(
    'invenio_pidrelations.versioning',
    __name__,
    template_folder='templates'
)


@versioning_blueprint.app_template_filter()
def to_versioning_api(pid, child=True):
    """Get PIDVersioning object."""
    return PIDVersioning(
        child=pid if child else None,
        parent=pid if not child else None
    )


__all__ = (
    'PIDVersioning',
    'versioning_blueprint'
)
