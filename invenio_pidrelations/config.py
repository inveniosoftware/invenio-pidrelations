# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

"""Invenio module that adds PID relations to the Invenio-PIDStore module."""

from collections import namedtuple

RelationType = namedtuple('RelationType',
                          ['id', 'name', 'label', 'api', 'schema'])

PIDRELATIONS_RELATION_TYPES = [
    RelationType(0, 'ordered', 'Ordered',
                 'invenio_pidrelations.api:PIDConceptOrdered',
                 'invenio_pidrelations.serializers.schemas.RelationSchema'),
    RelationType(1, 'unordered', 'Unordered',
                 'invenio_pidrelations.api:PIDConcept',
                 'invenio_pidrelations.serializers.schemas.RelationSchema'),
    RelationType(2, 'version', 'Version',
                 'invenio_pidrelations.contrib.versioning:PIDVersioning',
                 'invenio_pidrelations.serializers.schemas.RelationSchema'),
    RelationType(3, 'record_draft', 'Record Draft',
                 'invenio_pidrelations.contrib.records:RecordDraft',
                 'invenio_pidrelations.serializers.schemas.RelationSchema'),
]


PIDRELATIONS_PRIMARY_PID_TYPE = 'recid'
"""Default PID type for relations."""

PIDRELATIONS_INDEX_RELATIONS = False
"""Enable or disable relations indexing."""

PIDRELATIONS_DEFAULT_VALUE = 'foobar'
"""Default value for the application."""

PIDRELATIONS_INDEXED_RELATIONS = dict(
    recid=dict(
        field='version',
        api='invenio_pidrelations.contrib.versioning:PIDVersioning',
        # FIXME: for now the API does not provide any way to know if a relation
        # is ordered or not. Thus we write it here.
        ordered=True,
    )
)
"""Default PID fetcher."""
