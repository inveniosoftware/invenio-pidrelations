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

"""Persistent identifier store and registration."""

from __future__ import absolute_import, print_function

import logging
from enum import Enum

from flask_babelex import gettext
from invenio_db import db
from speaklater import make_lazy_gettext
from sqlalchemy.orm import backref
from sqlalchemy_utils.models import Timestamp
from sqlalchemy_utils.types import ChoiceType
from sqlalchemy.exc import IntegrityError

from invenio_pidstore.models import PersistentIdentifier, PIDStatus

_ = make_lazy_gettext(lambda: gettext)

logger = logging.getLogger('invenio-pidstore')


PIDRELATION_TYPE_TITLES = {
    'VERSION': _('Version'),
    'COLLECTION': _('Collection'),
}


class RelationType(Enum):
    """Constants for possible status of any given PID."""

    VERSION = 'V'
    """Two PIDs are subsequent versions of one another."""

    COLLECTION = 'C'
    """PIDs are aggregated into a collection of PIDs."""

    def __init__(self, value):
        """Hack."""

    def __eq__(self, other):
        """Equality test."""
        return self.value == other

    def __str__(self):
        """Return its value."""
        return self.value

    @property
    def title(self):
        """Return human readable title."""
        return PIDRELATION_TYPE_TITLES[self.name]


class PIDRelation(db.Model, Timestamp):
    """Store and register persistent identifiers.

    Assumptions:
      * Persistent identifiers can be represented as a string of max 255 chars.
      * An object has many persistent identifiers.
      * A persistent identifier has one and only one object.
    """

    __tablename__ = 'pidrelations_pidrelation'

    id = db.Column(db.Integer, primary_key=True)
    """Id of persistent identifier entry."""

    parent_pid_id = db.Column(
        db.Integer,
        db.ForeignKey(PersistentIdentifier.id, onupdate="CASCADE",
                      ondelete="RESTRICT"),
        nullable=False)

    child_pid_id = db.Column(
        db.Integer,
        db.ForeignKey(PersistentIdentifier.id, onupdate="CASCADE",
                      ondelete="RESTRICT"),
        nullable=False)

    relation_type = db.Column(ChoiceType(RelationType, impl=db.CHAR(1)),
                              nullable=False)
    """Type of relation between the parent and child PIDs."""

    order = db.Column(db.Integer, nullable=True)
    """Order in which the PID relations (e.g.: versions sequence)."""

    #
    # Relations
    #
    parent_pid = db.relationship(
        PersistentIdentifier,
        primaryjoin=PersistentIdentifier.id == parent_pid_id,
        backref=backref('child_pids', lazy='dynamic'))

    child_pid = db.relationship(
        PersistentIdentifier,
        primaryjoin=PersistentIdentifier.id == child_pid_id,
        backref=backref('parent_pids', lazy='dynamic'))

    @classmethod
    def create(cls, parent_pid, child_pid, relation_type, order):

        try:
            with db.session.begin_nested():
                obj = cls(parent_pid_id=parent_pid.id,
                          child_pid_id=child_pid.id,
                          relation_type=relation_type,
                          order=order)
                db.session.add(obj)
                # logger.info("Created PIDRelation {obj.parent_pid_id} -> "
                #             "{obj.child_pid_id} ({obj.relation_type}, "
                #             "order:{obj.order})".format(obj=obj))
        except IntegrityError:
            raise Exception("PID Relation already exists.")
            # msg = "PIDRelation already exists: " \
            #       "{0} -> {1} ({2})".format(
            #         parent_pid, child_pid, relation_type)
            # logger.exception(msg)
            # raise Exception(msg)

    @classmethod
    def create_head_pid(cls, pid, head_pid_value):
        """
        Create a Head PID for the Version PID.

        :param pid: Version PID for which a Head PID should be created.
        :type pid: invenio_pidstore.models.PersistentIdentifier
        :param head_pid_value: Head PID value of the new Head PID
        :type head_pid_value: str
        :return: Resulting Head PID and PIDRelation object (tuple)
        :rtype: (PersistentIdentifier, PIDRelation)
        """
        # Create new pid here of type 'HEAD'
        # Create a PID redirect
        head_pid = PersistentIdentifier.create(
            pid_type=pid.pid_type,
            pid_value=head_pid_value,
            object_type='hed',
            status=PIDStatus.REGISTERED
        )
        return head_pid, cls.create(head_pid, pid, RelationType.VERSION, 0)

    @staticmethod
    def is_head_pid(pid):
        """Determine if 'pid' is a Head PID."""
        return db.session.query(PIDRelation).join(
            PersistentIdentifier,
            PIDRelation.parent_pid_id == PersistentIdentifier.id
        ).filter(
            PersistentIdentifier.id == pid.id,
            PIDRelation.relation_type == RelationType.VERSION
        ).count() > 0

    @classmethod
    def get_head_pid(cls, pid):
        """
        Get the Head PID of a PID in the argument.

        If 'pid' is already the Head PID, return it, otherwise
        return the Head PID as defined in the relation table.
        In case the PID does not have a Head PID, return None.
        """
        if cls.is_head_pid(pid):
            return pid
        else:
            q = db.session.query(PIDRelation).filter(
                PIDRelation.child_pid_id == pid.id,
                PIDRelation.relation_type == RelationType.VERSION
            )
            if q.count() == 0:
                return None
            else:
                return PersistentIdentifier.query.get(q.one().parent_pid_id)

    @staticmethod
    def is_version_pid(pid):
        """
        Determine if 'pid' is a Version PID.
        """
        db.session.query(PIDRelation).filter(
            PIDRelation.child_pid_id == pid.id,
            PIDRelation.relation_type == RelationType.VERSION
        ).count() > 0
        return bool(pid.parent_pids)

    @staticmethod
    def is_latest_pid(pid):
        """
        Determine if 'pid' is the latest version of a resource.
        """
        # if is_head_pid(pid):
        #   return True
        # else:
        #   latest_pid = cls.get_latest_pid(pid)
        #   if latest_pid is None:
        #       raise("Not a versioned PID")
        #   return latest_pid.id == pid.id
        pass

    @classmethod
    def get_latest_pid(cls, pid):
        """
        Get the latest PID as pointed by the Head PID.

        If the 'pid' is a Head PID, return the latest of its children.
        If the 'pid' is a Version PID, return the latest of its siblings.
        Return None for the non-versioned PIDs.
        """

        head = cls.get_head_pid(pid)
        head.child_pids.order_by(PIDRelation.order).first()
        # if is_head_pid(pid):
        #    return JOIN(PID, PIDRelation, PID.id == PIDRelation.parent_pid_id)
        #       .filter(
        #       relation_type=RelationType.version,
        #       PID.id == pid.id
        #       ).sort(PIDRelation.order).first().child_pid
        # else:
        #    return cls.get_latest_pid(cls.get_head_pid(pid))
        pass

    @staticmethod
    def get_all_version_pids(pid):
        """
        Works both for Head PIDS (return the children) and Version PIDs (return
        all sibling including self)
        """
        # head = get_head_pid(pid)
        # head.child_pids.order_by(PIDRelation.order)
        pass

    @staticmethod
    def append_version_pid(pidA, pidB):
        pass
        # Create a relationship between parent
        # return cls.insert_version_pid(head_pid, pid, -1)
        pass

    @staticmethod
    def insert_version_pid(head_pid, pid, index):
        pass

    @staticmethod
    def remove_version_pid(pid):
        pass


__all__ = (
    'PIDRelation',
    'RelationType',
)
