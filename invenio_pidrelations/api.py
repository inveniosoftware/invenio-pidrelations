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

from werkzeug.utils import cached_property
from flask_sqlalchemy import BaseQuery
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased

from .models import PIDRelation


class PIDQuery(BaseQuery):
    """Query used by PIDNodes APIs when requesting related PIDs."""

    def __init__(self, entities, session,
                 _filtered_pid_class=PersistentIdentifier):
        """Constructor.

        :param _filtered_pid_class: SQLAlchemy Model class which is used for
        status filtering.
        """
        super(PIDQuery, self).__init__(entities, session)
        self._filtered_pid_class = _filtered_pid_class

    def ordered(self, ord='desc'):
        """Order the query result on the relations' indexes."""
        if ord not in ('asc', 'desc', ):
            raise
        ord_f = getattr(PIDRelation.index, ord)()
        return self.order_by(ord_f)

    def status(self, status_in):
        """Filter the PIDs based on their status."""
        if isinstance(status_in, PIDStatus):
            status_in = [status_in, ]
        return self.filter(
            self._filtered_pid_class.status.in_(status_in)
        )


def resolve_pid(fetched_pid):
    """Retrieve the real PID given a fetched PID.

    :param pid: fetched PID to resolve.
    """
    return PersistentIdentifier.get(
        pid_type=fetched_pid.pid_type,
        pid_value=fetched_pid.pid_value,
        pid_provider=fetched_pid.provider.pid_provider
    )


class PIDNode(object):
    """PID Node API.

    A node can have multiple parents and multiple children for a given
    relation_type.
    """

    def __init__(self, pid, relation_type):
        """Constructor."""
        super(PIDNode, self).__init__()
        self.relation_type = relation_type
        self.pid = pid

    @cached_property
    def _resolved_pid(self):
        """Resolve the pid provided to the constructor if it is a fetched pid.
        """
        if not isinstance(self.pid, PersistentIdentifier):
            return resolve_pid(self.pid)
        return self.pid

    def _get_child_relation(self, child_pid):
        """Retrieve the relation between this node and a child PID."""
        return PIDRelation.query.filter_by(
            parent=self._resolved_pid,
            child=child_pid,
            relation_type=self.relation_type.id).one()

    def _connected_pids(self, from_parent=True):
        """Follow a relationship to find connected PIDs.abs.

        :param from_parent: search children from the current pid if True, else
        search for its parents.
        :type from_parent: bool
        """
        to_pid = aliased(PersistentIdentifier, name='to_pid')
        if from_parent:
            to_relation = PIDRelation.child_id
            from_relation = PIDRelation.parent_id
        else:
            to_relation = PIDRelation.parent_id
            from_relation = PIDRelation.child_id
        query = PIDQuery(
            [to_pid], db.session(),
        ).join(
            PIDRelation,
            to_pid.id == to_relation
        )
        # accept both PersistentIdentifier models and fake PIDs with just
        # pid_value, pid_type as they are fetched with the PID fetcher.
        if isinstance(self.pid, PersistentIdentifier):
            query = query.filter(from_relation == self.pid.id)
        else:
            from_pid = aliased(PersistentIdentifier, name='from_pid')
            query = query.join(
                from_pid,
                from_pid.id == from_relation
            ).filter(
                from_pid.pid_value == self.pid.pid_value,
                from_pid.pid_type == self.pid.pid_type,
            )

        return query

    @property
    def parents(self):
        """Retrieves all parent PIDs."""
        return self._connected_pids(from_parent=False)

    @property
    def children(self):
        """Retrieves all child PIDs."""
        return self._connected_pids(from_parent=True)

    @property
    def is_parent(self):
        """Test if the given PID has any children."""
        return db.session.query(self.children.exists()).scalar()

    @property
    def is_child(self):
        """Test if the given PID has any parents."""
        return db.session.query(self.parents.exists()).scalar()

    def insert_child(self, child_pid):
        """Add the given PID to the list of children PIDs."""
        try:
            # TODO: Here add the check for the max parents and the max children
            with db.session.begin_nested():
                if not isinstance(child_pid, PersistentIdentifier):
                    child_pid = resolve_pid(child_pid)
                return PIDRelation.create(
                    self._resolved_pid, child_pid, self.relation_type.id, None
                )
        except IntegrityError:
            raise Exception("PID Relation already exists.")

    def remove_child(self, child_pid):
        """Remove a child from a PID concept."""
        with db.session.begin_nested():
            if not isinstance(child_pid, PersistentIdentifier):
                child_pid = resolve_pid(child_pid)
            relation = PIDRelation.query.filter_by(
                parent=self._resolved_pid,
                child=child_pid,
                relation_type=self.relation_type.id).one()
            db.session.delete(relation)


class PIDNodeOrdered(PIDNode):
    """PID Node API.

    A node can have multiple parents and multiple children for a given
    relation_type.
    """

    def index(self, child_pid):
        """Index of the child in the relation."""
        if not isinstance(child_pid, PersistentIdentifier):
            child_pid = resolve_pid(child_pid)
        relation = PIDRelation.query.filter_by(
            parent=self._resolved_pid,
            child=child_pid,
            relation_type=self.relation_type.id).one()
        return relation.index

    @property
    def is_last_child(self, child_pid):
        """
        Determine if 'pid' is the latest version of a resource.

        Resolves True for Versioned PIDs which are the oldest of its siblings.
        False otherwise, also for Head PIDs.
        """
        last_child = self.last_child
        if last_child is None:
            return False
        return last_child == child_pid

    @property
    def last_child(self):
        """
        Get the latest PID as pointed by the Head PID.

        If the 'pid' is a Head PID, return the latest of its children.
        If the 'pid' is a Version PID, return the latest of its siblings.
        Return None for the non-versioned PIDs.
        """
        return self.children.filter(
            PIDRelation.index.isnot(None)).ordered().first()

    def next_child(self, child_pid):
        """Get the next child PID in the PID relation."""
        relation = self._get_child_relation(child_pid)
        if relation.index is not None:
            return self.children.filter(
                PIDRelation.index > relation.index
            ).ordered(ord='asc').first()
        else:
            return None

    def previous_child(self, child_pid):
        """Get the previous child PID in the PID relation."""
        relation = self._get_child_relation(child_pid)
        if relation.index is not None:
            return self.children.filter(
                PIDRelation.index < relation.index
            ).ordered(ord='desc').first()
        else:
            return None

    def insert_child(self, child_pid, index=-1):
        """Insert a new child into a PID concept.

        Argument 'index' can take the following values:
            0,1,2,... - insert child PID at the specified position
            -1 - insert the child PID at the last position
            None - insert child without order (no re-ordering is done)

            NOTE: If 'index' is specified, all sibling relations should
                  have PIDRelation.index information.

        """
        if index is None:
            index = -1
        try:
            with db.session.begin_nested():
                if not isinstance(child_pid, PersistentIdentifier):
                    child_pid = resolve_pid(child_pid)
                child_relations = self._resolved_pid.child_relations.filter(
                    PIDRelation.relation_type == self.relation_type.id
                ).order_by(PIDRelation.index).all()
                relation_obj = PIDRelation.create(
                    self._resolved_pid, child_pid, self.relation_type.id, None)
                if index == -1:
                    child_relations.append(relation_obj)
                else:
                    child_relations.insert(index, relation_obj)
                for idx, c in enumerate(child_relations):
                    c.index = idx
        except IntegrityError:
            raise Exception("PID Relation already exists.")

    def remove_child(self, child_pid, reorder=False):
        """Remove a child from a PID concept."""
        super(PIDNodeOrdered, self).remove_child(child_pid)
        child_relations = self._resolved_pid.child_relations.filter(
            PIDRelation.relation_type == self.relation_type.id).order_by(
                PIDRelation.index).all()
        if reorder:
            for idx, c in enumerate(child_relations):
                c.index = idx


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
        if self.relation_type is not None:
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
    def is_ordered(self):
        """Determine if the concept is an ordered concept."""
        return all(val is not None for val in self.children.with_entities(
            PIDRelation.index))

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

    def get_children(self, ordered=False, pid_status=None):
        """Get all children of the parent."""
        filter_cond = [PIDRelation.parent_id == self.parent.id, ]
        if pid_status is not None:
            filter_cond.append(PersistentIdentifier.status == pid_status)
        if self.relation_type is not None:
            filter_cond.append(PIDRelation.relation_type == self.relation_type)

        q = db.session.query(PersistentIdentifier).join(
            PIDRelation,
            PIDRelation.child_id == PersistentIdentifier.id
        ).filter(*filter_cond)
        if ordered:
            return q.order_by(PIDRelation.index.asc())
        else:
            return q

    @property
    def children(self):
        """Children of the parent."""
        return self.get_children()

    @property
    def has_children(self):
        """Determine if there are any children in this relationship."""
        return self.children.count() > 0

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

    @property
    def is_child(self):
        """
        Determine if 'pid' is a Version PID.

        Resolves as True for any PID which has a Head PID, False otherwise.
        """
        return self.has_parents

    def remove_child(self, child, reorder=False):
        """Remove a child from a PID concept."""
        with db.session.begin_nested():
            relation = PIDRelation.query.filter_by(
                parent_id=self.pid.id,
                child_id=child.id,
                relation_type=self.relation_type).one()
            db.session.delete(relation)
            if reorder:
                child_relations = self.pid.child_relations.filter(
                    PIDRelation.relation_type == self.relation_type).order_by(
                        PIDRelation.index).all()
                for idx, c in enumerate(child_relations):
                    c.index = idx


class PIDConceptOrdered(PIDConcept):
    """Standard PID Concept with childred ordering."""

    @property
    def children(self):
        """Overwrite the children property to always return them ordered."""
        return self.get_children(ordered=True)

    @property
    def is_ordered(self):
        """Determine if the concept is an ordered concept."""
        return True


__all__ = (
    'PIDNode',
    'PIDNodeOrdered',
    'PIDConcept',
    'PIDConceptOrdered',
)
