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

"""Persistent identifier's relations models."""

from __future__ import absolute_import, print_function

import logging
from enum import Enum

from flask_babelex import gettext
from invenio_db import db
from speaklater import make_lazy_gettext
from sqlalchemy.orm import backref
from sqlalchemy_utils.models import Timestamp
from sqlalchemy_utils.types import ChoiceType

from invenio_pidstore.models import PersistentIdentifier

_ = make_lazy_gettext(lambda: gettext)

logger = logging.getLogger('invenio-pidrelations')


PIDRELATION_TYPE_TITLES = {
    'VERSION': _('Version'),
    'COLLECTION': _('Collection'),
}


class RelationType(Enum):
    """Constants for possible status of any given PID."""

    VERSION = 0
    """Two PIDs are subsequent versions of one another."""

    COLLECTION = 1
    """PIDs are aggregated into a collection of PIDs."""

    def __init__(self, value):
        """Hack."""

    def __eq__(self, other):
        """Equality test."""
        return self.value == other

    def __str__(self):
        """Return its name."""
        return self.name

    @property
    def title(self):
        """Return human readable title."""
        return PIDRELATION_TYPE_TITLES[self.name]


class PIDRelation(db.Model, Timestamp):
    """Model persistent identifier relations."""

    __tablename__ = 'pidrelations_pidrelation'

    # TODO: Remove explicit PK
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

    relation_type = db.Column(db.SmallInteger(), nullable=False)
    """Type of relation between the parent and child PIDs."""

    order = db.Column(db.Integer, nullable=True)
    """Order in which the PID relations (e.g.: versions sequence)."""

    #
    # Relations
    #
    parent_pid = db.relationship(
        PersistentIdentifier,
        primaryjoin=PersistentIdentifier.id == parent_pid_id,
        backref=backref('child_relations', lazy='dynamic'))

    child_pid = db.relationship(
        PersistentIdentifier,
        primaryjoin=PersistentIdentifier.id == child_pid_id,
        backref=backref('parent_relations', lazy='dynamic'))

    def __repr__(self):
        return "<PIDRelation: {parent} -> {child} ({type}, {order})>".format(
            parent=self.parent_pid.pid_value,
            child=self.child_pid.pid_value,
            type=RelationType(self.relation_type),
            order=self.order)

    @classmethod
    def create(cls, parent_pid, child_pid, relation_type, order=None):
        """Create a PID relation for given parent and child."""

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
        return obj


__all__ = (
    'PIDRelation',
    'RelationType',
)
