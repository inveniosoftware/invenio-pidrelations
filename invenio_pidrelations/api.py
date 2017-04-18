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

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.exc import IntegrityError

from .models import PIDRelation
from .utils import resolve_relation_type_config


class PIDConcept(object):
    """API for PID version relations."""

    def __init__(self, child=None, parent=None, relation_type=None,
                 relation=None):
        """Create a PID concept API object."""
        if relation:
            self.relation = relation
            self.child = relation.child
            self.parent = relation.parent
            self.relation_type = relation.relation_type
        else:
            self.child = child
            self.parent = parent
            self.relation_type = relation_type
            # If child and parent (primary keys) are not None,
            # try to set the relation
            if child and parent:
                self.relation = PIDRelation.query.get(
                    (self.parent.id, self.child.id))
            else:
                self.relation = None

    @property
    def parents(self):
        """Return the PID parents for given relation."""
        filter_cond = [PIDRelation.child_id == self.child.id, ]
        if self.relation_type:
            filter_cond.append(PIDRelation.relation_type == self.relation_type)
        return db.session.query(PersistentIdentifier).join(
            PIDRelation,
            PIDRelation.parent_id == PersistentIdentifier.id
        ).filter(*filter_cond)

    @property
    def exists(self):
        """Determine if a PID Concept exists.

        Determine if constructed API object describes an existing PID Concept.
        The definition of that will vary across different PID Concepts, but
        it's intended use is to check if given child/parent PIDs are in
        the described relation.
        """
        return bool(self.relation)

    @property
    def has_parents(self):
        """Determine if there are any parents in this relationship."""
        return self.parents.count() > 0

    @property
    def parent(self):
        """Return the parent of the PID in given relation.

        NOTE: Not supporting relations, which allow for multiple parents,
              e.g. Collection.

        None if not found
        Raises 'sqlalchemy.orm.exc.MultipleResultsFound' for multiple parents.
        """
        if self._parent is None:
            parent = self.parents.one_or_none()
            self._parent = parent
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def is_parent(self):
        """Determine if the provided parent is a parent in the relation."""
        return self.has_children

    def get_children(self, pid_status=None):
        """Get all children of the parent."""
        filter_cond = [PIDRelation.parent_id == self.parent.id, ]
        if pid_status is not None:
            filter_cond.append(PersistentIdentifier.status == pid_status)
        if self.relation_type:
            filter_cond.append(PIDRelation.relation_type == self.relation_type)

        return db.session.query(PersistentIdentifier).join(
            PIDRelation,
            PIDRelation.child_id == PersistentIdentifier.id
        ).filter(*filter_cond)

    @property
    def children(self):
        """Children of the parent."""
        return self.get_children()

    @property
    def has_children(self):
        """Determine if there are any children in this relationship."""
        return self.children.count() > 0

    @property
    def is_child(self):
        """
        Determine if 'pid' is a Version PID.

        Resolves as True for any PID which has a Head PID, False otherwise.
        """
        return self.has_parents

    def add_child(self, child):
        """Add a new child into a PID concept."""
        try:
            with db.session.begin_nested():
                return PIDRelation.create(
                    self.parent, child, self.relation_type, None)
            # TODO: self.child = child
            # TODO: mark 'children' cached_property as dirty
        except IntegrityError:
            raise Exception("PID Relation already exists.")

    def remove_child(self, child):
        """Remove a child from a PID concept."""
        with db.session.begin_nested():
            relation = PIDRelation.query.filter_by(
                parent_id=self.parent.id,
                child_id=child.id,
                relation_type=self.relation_type).one()
            db.session.delete(relation)
        # TODO: self.child = None
        # TODO: mark 'children' cached_property as dirty


class PIDConceptOrdered(PIDConcept):
    """Standard PID Concept with childred ordering."""

    def get_children(self, pid_status=None, order='asc'):
        """Get all children of the parent."""
        q = super(PIDConceptOrdered, self).__init__(pid_status)
        if order is not None:
            if order == 'asc':
                return q.order_by(PIDRelation.index.asc())
            else:
                return q.order_by(PIDRelation.index.desc())
        return q

    def add_child(self, child, index=-1):
        """Add a new child into a PID concept.

        Argument 'index' can take the following values:
            0,1,2,... - insert child PID at the specified position
            -1 - insert the child PID at the last position
            None - insert child without order (no re-ordering is done)

            NOTE: If 'index' is specified, all sibling relations should
                  have PIDRelation.index information.

        """
        try:
            with db.session.begin_nested():
                child_relations = self.parent.child_relations.filter(
                    PIDRelation.relation_type ==
                    self.relation_type).order_by(PIDRelation.index).all()
                relation_obj = PIDRelation.create(
                    self.parent, child, self.relation_type, None)
                if index == -1:
                    child_relations.append(relation_obj)
                else:
                    child_relations.insert(index, relation_obj)
                for idx, c in enumerate(child_relations):
                    c.index = idx
            # TODO: self.child = child
            # TODO: mark 'children' cached_property as dirty
        except IntegrityError:
            raise Exception("PID Relation already exists.")

    def remove_child(self, child, reorder=False):
        """Remove a child from a PID concept."""
        with db.session.begin_nested():
            relation = PIDRelation.query.filter_by(
                parent_id=self.parent.id,
                child_id=child.id,
                relation_type=self.relation_type).one()
            db.session.delete(relation)
            if reorder:
                child_relations = self.parent.child_relations.filter(
                    PIDRelation.relation_type == self.relation_type).order_by(
                        PIDRelation.index).all()
                for idx, c in enumerate(child_relations):
                    c.index = idx
        # TODO: self.child = None
        # TODO: mark 'children' cached_property as dirty

    @property
    def index(self):
        """Index of the child in the relation."""
        return self.relation.index

    @property
    def is_last_child(self):
        """
        Determine if 'pid' is the latest version of a resource.

        Resolves True for Versioned PIDs which are the oldest of its siblings.
        False otherwise, also for Head PIDs.
        """
        last_child = self.last_child
        if last_child is None:
            return False
        return last_child == self.child

    @property
    def last_child(self):
        """
        Get the latest PID as pointed by the Head PID.

        If the 'pid' is a Head PID, return the latest of its children.
        If the 'pid' is a Version PID, return the latest of its siblings.
        Return None for the non-versioned PIDs.
        """
        return self.get_children(ordered=False).filter(
            PIDRelation.index.isnot(None)).order_by(
                PIDRelation.index.desc()).first()

    @property
    def next(self):
        """Get the next sibling in the PID relation."""
        if self.relation.index is not None:
            return self.children.filter_by(
                index=self.relation.index + 1).one_or_none()
        else:
            return None

    @property
    def previous(self):
        """Get the previous sibling in the PID relation."""
        if self.relation.index is not None:
            return self.children.filter_by(
                index=self.relation.index - 1).one_or_none()
        else:
            return None

__all__ = (
    'PIDConcept',
    'PIDConceptOrdered',
)
