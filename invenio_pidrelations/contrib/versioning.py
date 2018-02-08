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

from flask import Blueprint
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidrelations.contrib.draft import PIDNodeDraft

from ..api import PIDNodeOrdered
from ..models import PIDRelation
from ..utils import resolve_relation_type_config
from ..errors import PIDRelationConsistencyError


class PIDNodeVersioning(PIDNodeOrdered):
    """API for PID versioning relations.

    parents (max: 1): a PID linked to all the versions of a record
                      and always redirecting to its last version.
    children (max: unlimited): PIDs of the different versions of a record.

    Children PIDs are separated in two categories: RESERVED and REGISTERED.

    There can be only one RESERVED PID. It is considered as the "draft" PID,
    i.e. the next version to publish. This draft/RESERVED PID is the parent PID
    of a "deposit" PID (see invenio-deposit). The PIDNodeDraft API is used in
    order to manipulate the relation between the draft PID and its child
    deposit PID.

    REGISTERED PIDs are published record PIDs which each represents a
    version of the original record.

    The parent PID's status is RESERVED as long as no Version is published,
    i.e. REGISTERED.
    """

    def __init__(self, pid):
        """Create a PID versioning API.

        :param pid: either the parent PID or a specific record version PID.
        """
        self.relation_type = resolve_relation_type_config('version')
        super(PIDNodeDraft, self).__init__(
            pid=pid, relation_type=self.relation_type,
            max_parents=1, max_children=None
        )

    @property
    def children(self):
        """Children of the parent."""
        return self.children.status(PIDStatus.REGISTERED)

    def insert_child(self, child, index=-1):
        """Insert a Version child PID."""
        if child.status == PIDStatus.RESERVED:
            raise PIDRelationConsistencyError(
                "Version PIDs should not have status 'RESERVED'. Use "
                "insert_draft_child to insert a draft PID.")
        with db.session.begin_nested():
            # if there is a draft and "child" is inserted as the last version,
            # it should be inserted before the draft.
            draft = self.draft_child
            if draft and index == -1:
                index = self.index(draft)
            super(PIDVersioning, self).insert_child(child, index=index)
            self.update_redirect()

    def remove_child(self, child):
        """Remove a Version child PID.

        Extends the base method call by redirecting from the parent to the
        last child.
        """
        if child.status == PIDStatus.RESERVED:
            raise PIDRelationConsistencyError(
                "Version PIDs should not have status 'RESERVED'. Use "
                "remove_draft_child to remove a draft PID.")
        with db.session.begin_nested():
            super(PIDVersioning, self).remove_child(child, reorder=True)
            self.update_redirect()

    @property
    def draft_child(self):
        """Get the draft (RESERVED) child."""
        return self.children.status(PIDStatus.RESERVED).one_or_none()

    @property
    def draft_child_deposit(self):
        """Get the deposit PID of the draft child.

        Return `None` if no draft child PID exists.
        """
        if self.draft_child:
            return PIDNodeDraft(self.draft_child).children.one_or_none()
        else:
            return None

    def insert_draft_child(self, child):
        """Insert a draft child to versioning."""
        if child.status != PIDStatus.RESERVED:
            raise PIDRelationConsistencyError(
                "Draft child should have status 'RESERVED'")

        if not self.draft_child:
            with db.session.begin_nested():
                super(PIDVersioning, self).insert_child(child, index=-1)
        else:
            raise PIDRelationConsistencyError(
                "Draft child already exists for this relation: {0}".format(
                    self.draft_child))

    def remove_draft_child(self):
        """Remove the draft child from versioning."""
        if self.draft_child:
            with db.session.begin_nested():
                super(PIDVersioning, self).remove_child(self.draft_child,
                                                        reorder=True)

    def update_redirect(self):
        """Update the parent redirect to the current last child.

        Use this method when the status of a PID changed (ex: draft changed
        from RESERVED to REGISTERED)
        """
        if self.last_child:
            if self.parent.status == PIDStatus.RESERVED:
                self.parent.register()
            self.parent.redirect(self.last_child)


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
