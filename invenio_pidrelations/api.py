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
from .errors import RelationConflictError, RelationNotFoundError


class PIDConcept(object):
    """API for PID concepts.

    A PID concept is a tree of depth 1 with a single parent PID and one or more
    children PIDs linked together by relations of one single type.

    A child PID can be part of multiple concepts, i.e. having multiple parents.
    The concept is defined by the parent PID and the relation type.

    Subclasses are allowed to extend this by adding multiple relation
    types but the additional relations should be accessed with custom methods.
    The definition of "children" should not change.
    """

    def __init__(self, parent=None, relation_type=None):
        """Create a PID concept API object.

        :param parent: parent PID of this concept.
        :param relation_type: type of the relations which link the parent PID
            to its children.
        """
        self.parent = parent
        self.relation_type = relation_type

    @classmethod
    def get(cls, parent=None, child=None, relation=None):
        """Retrieve a PIDConcept.

        Parameters parent and child or relation must be provided.

        :param parent: parent PID, ignored if relation is set.
        :param child: child PID, ignored if relation is set.
        :param relation: relation which is part of this PIDConcept. It's
            parent PID and relation_type will be used.
        :type relation: :py:class:`.models.PIDRelation`

        :returns: a PIDConcept or None if no relation is found between parent
            and child PIDs.
        """
        if not (parent or child) and not relation:
            raise ValueError('Retrieving a PIDConcept requires an existing'
                             'parent and child PID or a relation')
        if not relation:
            relation = PIDRelation.query.get(parent.id, child.id).one_or_none()
        if relation is None:
            return None
        return cls(parent=relation.parent,
                   relation_type=relation.relation_type)

    def get_children(self):
        """Get all children of the parent.

        :returns: an SQLAlchemy query which queries for all children PIDs.
        """
        return db.session.query(PersistentIdentifier).join(
            PIDRelation,
            PIDRelation.child_id == PersistentIdentifier.id
        ).filter(PIDRelation.parent_id == self.parent.id,
                 PIDRelation.relation_type == self.relation_type)

    @property
    def has_children(self):
        """Determine if there are any children in this concept."""
        return self.get_children().count() > 0

    def has_child(pid):
        """Check if the provided PID is a child of this concept.

        :returns: True if the given PID is a child in this concept,
            else False.
        """
        return PIDRelation.query.get(self.parent.id, pid).exists()

    def add_child(self, child):
        """Add a new child into a PID concept."""
        try:
            with db.session.begin_nested():
                return PIDRelation.create(
                    self.parent, child, self.relation_type, None)
        except IntegrityError:
            raise RelationConflictError("PID Relation already exists.")

    def remove_child(self, child):
        """Remove a child from a PID concept."""
        with db.session.begin_nested():
            relation = PIDRelation.query.filter_by(
                parent_id=self.parent.id,
                child_id=child.id,
                relation_type=self.relation_type).one()
            db.session.delete(relation)
            # FIXME: raise RelationNotFoundError if delete fails


class PIDConceptOrdered(PIDConcept):
    """Standard PID Concept with children ordering."""

    def get_children(self, order=None):
        """Get all children of the parent.

        :param order: "asc" if the query should be sorted in ascending order,
            "desc" if the ordering should be descending, None for no ordering.
        """
        q = super(PIDConceptOrdered, self).__init__()
        if order is not None:
            if order == 'asc':
                return q.order_by(PIDRelation.index.asc())
            else:
                return q.order_by(PIDRelation.index.desc())
        return q

    def add_child(self, child, index=-1):
        """Link a PID as a child to this concept's parent.

        :param child: PID for which a new relation will be created.
        :param index: valuse in [0:n] will insert child PID at the specified
          position, -1 will insert the child PID at the last position, None
          will insert child without order (no re-ordering is done).
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
        except IntegrityError:
            raise RelationConflictError("PID Relation already exists.")

    def remove_child(self, child, reorder=False):
        """Remove the relation linking a child PID to this concept's parent.

        :param child: PID whose relation will be removed.
        :param reorder: enable reordering of siblings by decrementing the
            index of every following relation.
        """
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

    @property
    def index_of(self, pid):
        """Index of the child in this concept.

        :param pid: a child PID.

        :returns: index of the given PID.
        """
        relation = PIDRelation.query.get(self.parent.id, pid.id).one_or_none()
        if relation is None or relation.relation_type != self.relation_type:
            raise RelationNotFoundError(
                'No relation of type {0} between {1} as parent PID and {2} '
                'as child PID'.format(self.relation_type, self.parent.id,
                                      pid.id)
            )
        return relation.index

    def get_child(index):
        """Retrieve the child at the given index.

        :param index: index of the retrieved child PID in this concept.
        :type index: int

        :returns: the child PID, None if no relation matches this index.
        """
        return self.get_children().filter(
            PIDRelation.index == index).one_or_none()

    @property
    def is_last_child(self, pid):
        """Determine if 'pid' is the latest child of this PIDConcept.

        :param pid: a child PID.

        :returns: True if the given PID has the highest index in this
            concept, False otherwise.
        """
        return self.last_child() == pid

    @property
    def last_child(self):
        """Get the child PID with the highest index.

        :returns: the last child PID. None there are no children PIDs.
        """
        return self.get_children(order='desc').first()

    @property
    def next(self, pid):
        """Get the next sibling in the PID relation.

        :param pid: child PID whose next sibling will be returned.

        :returns: PID whose index follows the one provided in this concept.
            None if there is no such PID.
        """
        index = self.index_of(pid)
        return self.get_child(index + 1)

    @property
    def previous(self, pid):
        """Get the previous sibling in the PID relation.

        :param pid: child PID whose previous sibling will be returned.

        :returns: PID whose index precedes the one provided in this concept.
            None if there is no such PID.
        """
        index = self.index_of(pid)
        return self.get_child(index - 1)

__all__ = (
    'PIDConcept',
    'PIDConceptOrdered',
)
