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

"""api query tests."""

import pytest
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from sqlalchemy.orm import aliased

from invenio_pidrelations.api import PIDQuery
from invenio_pidrelations.models import PIDRelation


@pytest.mark.parametrize("order, sort", [
    # Test default value, i.e. "desc"
    ({}, lambda children: list(reversed(children))),
    ({'ord': 'asc'}, lambda children: children),
    ({'ord': 'desc'}, lambda children: list(reversed(children)))
])
def test_query_order(db, version_pids, order, sort):
    """Test PIDQuery.order()."""
    result = PIDQuery([PersistentIdentifier], db.session()).join(
        PIDRelation,
        PersistentIdentifier.id == PIDRelation.child_id
    ).filter(
        PIDRelation.parent_id == version_pids[0]['parent'].id
    ).ordered(**order).all()
    assert result == sort(version_pids[0]['children'])


@pytest.mark.parametrize("status, filt", [
    (
        # Test with a PIDStatus
        PIDStatus.REGISTERED,
        lambda children: [child for child in children if child.status in [
            PIDStatus.REGISTERED
        ]]
    ),
    (
        # Test with a list of PIDStatus
        [PIDStatus.REGISTERED, PIDStatus.DELETED],
        lambda children: [child for child in children if child.status in [
            PIDStatus.REGISTERED, PIDStatus.DELETED
        ]]
    ),
])
def test_query_status(db, version_pids, status, filt):
    """Test PIDQuery.status()."""
    # test with simple join
    result = PIDQuery([PersistentIdentifier], db.session()).join(
        PIDRelation,
        PersistentIdentifier.id == PIDRelation.child_id
    ).filter(
        PIDRelation.parent_id == version_pids[0]['parent'].id
    ).status(status).ordered('asc').all()
    assert result == filt(version_pids[0]['children'])

    # test with double join (parent and child PID)
    parent_pid = aliased(PersistentIdentifier, name='parent_pid')
    child_pid = aliased(PersistentIdentifier, name='child_pid')
    result2 = PIDQuery(
        [child_pid], db.session(), _filtered_pid_class=child_pid
    ).join(
        PIDRelation,
        child_pid.id == PIDRelation.child_id
    ).join(
        parent_pid,
        parent_pid.id == PIDRelation.parent_id
    ).filter(
        parent_pid.pid_value == version_pids[0]['parent'].pid_value
    ).status(status).ordered(ord='asc').all()
    assert result == filt(version_pids[0]['children'])
