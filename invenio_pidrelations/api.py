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
from sqlalchemy.exc import IntegrityError
from .models import PIDRelation, RelationType


class PIDConcept(object):
    """API for PID version relations."""

    def __init__(self, child=None, parent=None, relation_type=None,
                 relation=None):
        # Construct either from (child, parent and relation_type)(PKs)
        # OR relation
        if relation:
            self.relation = relation
            self.child = relation.child
            self.parent = relation.parent
            self.relation_type = relation.relation_type
        else:
            self.child = child
            self.parent = parent
            self.relation_type = relation_type
            if all(arg is not None for arg in (child, parent, relation_type)):
                pass
                # self.relation = PIDRelation.query.get(...)
            # NOTE: Do not query.filter(...) with partial information
            # as you might guess wrong if the relation does not exist

    #
    # Classmethods
    #
    @classmethod
    def is_child(cls, pid, relation_type):
        """
        Determine if 'pid' is a Version PID.

        Resolves as True for any PID which has a Head PID, False otherwise.
        """
        return cls.get_parents(pid, relation_type).count() == 1

    @classmethod
    def is_parent(cls, pid, relation_type):
        """Determine if PID is a Parent in given relation type."""
        return cls(parent=pid, relation_type=relation_type).has_children()

    @staticmethod
    def get_parents(pid, relation_type):
        """Return the PID parents for given relation."""
        return db.session.query(PersistentIdentifier).join(
            PIDRelation,
            PIDRelation.parent_pid_id == PersistentIdentifier.id
        ).filter(
            PIDRelation.child_pid_id == pid.id,
            PIDRelation.relation_type == relation_type
        )

    @classmethod
    def get_parent(cls, pid, relation_type):
        """Return the parent of the PID in given relation.

        NOTE: Not supporting relations, which allow for multiple parents,
              e.g. Collection.

        None is not found
        """
        q = cls.parents(pid, relation_type)
        if q.count() > 1:
            raise Exception("PID has more than one parent for this relation.")
        else:
            return q.first()

    #
    # Instance methods
    #
    # TODO: cached property
    def children(self, ordered=True):
        q = db.session.query(PersistentIdentifier).join(
            PIDRelation,
            PIDRelation.child_pid_id == PersistentIdentifier.id
        ).filter(
            PIDRelation.parent_pid_id == self.parent.id,
            PIDRelation.relation_type == self.relation_type
        )
        if ordered:
            return q.order_by(PIDRelation.order)
        else:
            return q

    def has_children(self):
        return self.children().count() > 0

    def insert(self, child, index=None):
        """
        Argument 'index' can take the following values:
            0,1,2,... - insert child PID at the specified position
            -1 - insert the child PID at the last position
            None - insert child without order (no re-ordering is done)

            NOTE: If 'index' is specified, all sibling relations should
                  have PIDRelation.order information.

        """
        try:
            with db.session.begin_nested():
                if index is not None:
                    children = self.parent.child_relations.filter(
                        PIDRelation.relation_type ==
                        self.relation_type).order_by(PIDRelation.order).all()
                    relation_obj = PIDRelation.create(
                        self.parent, child, self.relation_type, None)
                    if index == -1:
                        children.append(relation_obj)
                    else:
                        children.insert(index, relation_obj)
                    for idx, c in enumerate(children):
                        c.order = idx
                else:
                    relation_obj = PIDRelation.create(
                        self.parent, child, self.relation_type, None)
            # TODO: self.child = child
            # TODO: mark 'children' cached_property as dirty
        except IntegrityError:
            raise Exception("PID Relation already exists.")

    def remove(self, reorder=False):
        """
        Removes a PID relation.
        """
        with db.session.begin_nested():
            relation = PIDRelation.query.filter_by(
                parent_pid_id=self.parent.id,
                child_pid_id=self.child.id,
                relation_type=self.relation_type).one()
            db.session.delete(relation)
            if reorder:
                children = self.parent.child_relations.filter(
                    PIDRelation.relation_type == self.relation_type).order_by(
                        PIDRelation.order).all()
                for idx, c in enumerate(children):
                    c.order = idx
        # TODO: self.child = None
        # TODO: mark 'children' cached_property as dirty

    def are_related(self):
        return PIDRelation.query.filter_by(
            child_pid_id=self.child.id,
            parent_pid_id=self.parent.id,
            relation_type=self.relation_type).count() > 0

    def create_relation(self, order=None):
        if not self.are_related():
            relation_obj = PIDRelation.create(
                self.parent, self.child, self.relation_type, order)
            return relation_obj
        # TODO: mark 'children' cached_property as dirty
        return None

    def create_parent(self, parent_pid_value):
        """
        Create a parent for this concept.

        Create a new PersistentIdentifier object, who will be a parent in this
        relation. This new PID, will inherit all PID properties of the child,
        except for the parent_pid_value, which is a required argument.

        :param parent_pid_value: Head PID value of the new Head PID
        :type parent_pid_value: str
        :return: Resulting Parent-Child PIDRelation object
        :rtype: PIDRelation
        """
        # TODO: make sure self.child is not None
        # TODO: make sure self.parent is None (raise)
        # TODO: Make sure no parent exists already in DB (raise)
        parent = PersistentIdentifier.create(
            pid_type=self.child.pid_type,
            pid_value=parent_pid_value,
            object_type=self.child.object_type,
            status=PIDStatus.REGISTERED
        )
        self.parent = parent
        relation = self.create_relation(order=0)
        return relation

    def is_last_child(self):
        """
        Determine if 'pid' is the latest version of a resource.

        Resolves True for Versioned PIDs which are the oldest of its siblings.
        False otherwise, also for Head PIDs.
        """
        last_child = self.get_last_child()
        if last_child is None:
            return False
        return last_child == self.child

    def get_last_child(self):
        """
        Get the latest PID as pointed by the Head PID.

        If the 'pid' is a Head PID, return the latest of its children.
        If the 'pid' is a Version PID, return the latest of its siblings.
        Return None for the non-versioned PIDs.
        """
        return self.parent.child_relations.order_by(
            PIDRelation.order.desc()).first().child_pid


__all__ = (
    'PIDConcept',
)
