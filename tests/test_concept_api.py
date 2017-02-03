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

"""Module tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier

from invenio_pidrelations.models import PIDRelation, RelationType
from invenio_pidrelations.api import PIDVersionRelation


def test_pidrelation(app, db):
    """Test version import."""
    pid = PersistentIdentifier.create('doi', 'foobar.v1')
    head_pid = PIDVersionRelation.create_head(pid, 'foobar')
    db.session.commit()

    assert head_pid.pid_value == 'foobar'
    assert head_pid.pid_type == pid.pid_type


def test_basic_api_methods(app, db, pids):

    # Test the "children" method (returns a query of PIDs)
    # Version PIDs
    h1, h1v1, h1v2, h2, h2v1, c1, c1r1, c1r2, pid1 = \
        (pids[p] for p in ['h1', 'h1v1', 'h1v2', 'h2', 'h2v1',
                           'c1', 'c1r1', 'c1r2', 'pid1'])
    assert PIDRelation.children(h1, RelationType.VERSION).count() == 2
    assert [h1v2, h1v1] == PIDRelation.children(h1, RelationType.VERSION,
                                                ordered=False).all()
    assert [h1v1, h1v2] == PIDRelation.children(h1, RelationType.VERSION,
                                                ordered=True).all()
    assert PIDRelation.children(h1v1, RelationType.VERSION).count() == 0
    # Collection PIDs
    assert PIDRelation.children(c1, RelationType.COLLECTION).count() == 2
    assert [c1r1, c1r2] == PIDRelation.children(
        c1, RelationType.COLLECTION).all()
    assert PIDRelation.children(c1r1, RelationType.COLLECTION).count() == 0
    # Regular PID
    assert PIDRelation.children(pid1, RelationType.VERSION).count() == 0

    # Test the "parents" method (returns a query of PIDs)
    assert PIDRelation.parents(h1, RelationType.VERSION).count() == 0
    assert h1 == PIDRelation.parents(h1v1, RelationType.VERSION).one()
    assert h1 == PIDRelation.parents(h1v2, RelationType.VERSION).one()

    # Test the "parent" method (returns a PID)
    assert h1 == PIDRelation.parent(h1v1, RelationType.VERSION)
    assert h1 == PIDRelation.parent(h1v2, RelationType.VERSION)

    # Test the "siblings" method (returns a query of PIDs)
    assert [h1v1, h1v2] == PIDRelation.siblings(
        h1v1, RelationType.VERSION, ordered=True).all()

    assert [h1v1, h1v2] == PIDRelation.siblings(
        h1v2, RelationType.VERSION, ordered=True).all()

    assert [c1r1, c1r2] == PIDRelation.siblings(
        c1r1, RelationType.COLLECTION, ordered=False).all()

    # Test "has_children", "has_parents"
    # Version PIDs
    assert PIDRelation.has_children(h1, RelationType.VERSION) is True
    assert PIDRelation.has_parents(h1, RelationType.VERSION) is False
    assert PIDRelation.has_children(h1v1, RelationType.VERSION) is False
    assert PIDRelation.has_parents(h1v1, RelationType.VERSION) is True

    # Collection PIDs
    assert PIDRelation.has_children(c1, RelationType.COLLECTION) is True
    assert PIDRelation.has_parents(c1, RelationType.COLLECTION) is False

    # Regular PIDs
    assert PIDRelation.has_children(pid1, RelationType.VERSION) is False
    assert PIDRelation.has_parents(pid1, RelationType.VERSION) is False

    # Test the "insert" method
    # Insert at the end (index=-1)
    PIDRelation.insert(h1, pid1, RelationType.VERSION, index=-1)
    assert [h1v1, h1v2, pid1] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    # Make sure relations are ordered correctly
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1_c[0].child_pid == h1v1
    assert h1_c[0].order == 0
    assert h1_c[1].child_pid == h1v2
    assert h1_c[1].order == 1
    assert h1_c[2].child_pid == pid1
    assert h1_c[2].order == 2

    PIDRelation.remove(h1, pid1, RelationType.VERSION, reorder=True)
    assert [h1v1, h1v2] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1_c[0].child_pid == h1v1
    assert h1_c[0].order == 0
    assert h1_c[1].child_pid == h1v2
    assert h1_c[1].order == 1

    # Insert at the first position
    PIDRelation.insert(h1, pid1, RelationType.VERSION, index=0)
    assert [pid1, h1v1, h1v2] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1_c[0].child_pid == pid1
    assert h1_c[0].order == 0
    assert h1_c[1].child_pid == h1v1
    assert h1_c[1].order == 1
    assert h1_c[2].child_pid == h1v2
    assert h1_c[2].order == 2

    PIDRelation.remove(h1, pid1, RelationType.VERSION, reorder=True)
    assert [h1v1, h1v2] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1_c[0].child_pid == h1v1
    assert h1_c[0].order == 0
    assert h1_c[1].child_pid == h1v2
    assert h1_c[1].order == 1

    # Insert at the second position
    PIDRelation.insert(h1, pid1, RelationType.VERSION, index=1)
    assert [h1v1, pid1, h1v2] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1_c[0].child_pid == h1v1
    assert h1_c[0].order == 0
    assert h1_c[1].child_pid == pid1
    assert h1_c[1].order == 1
    assert h1_c[2].child_pid == h1v2
    assert h1_c[2].order == 2

    PIDRelation.remove(h1, pid1, RelationType.VERSION, reorder=True)
    assert [h1v1, h1v2] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1_c[0].child_pid == h1v1
    assert h1_c[0].order == 0
    assert h1_c[1].child_pid == h1v2
    assert h1_c[1].order == 1

    # Insert at the last position
    PIDRelation.insert(h1, pid1, RelationType.VERSION, index=100)
    assert [h1v1, h1v2, pid1] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1_c[0].child_pid == h1v1
    assert h1_c[0].order == 0
    assert h1_c[1].child_pid == h1v2
    assert h1_c[1].order == 1
    assert h1_c[2].child_pid == pid1
    assert h1_c[2].order == 2

    PIDRelation.remove(h1, pid1, RelationType.VERSION, reorder=True)
    assert [h1v1, h1v2] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1_c[0].child_pid == h1v1
    assert h1_c[0].order == 0
    assert h1_c[1].child_pid == h1v2
    assert h1_c[1].order == 1

    PIDRelation.remove(h1, h1v1, RelationType.VERSION, reorder=True)
    assert [h1v2] == PIDRelation.children(
        h1, RelationType.VERSION, ordered=True).all()
    h1_c = h1.child_relations.order_by(PIDRelation.order).all()
    assert h1.child_relations.count() == 1
    assert h1_c[0].child_pid == h1v2
    assert h1_c[0].order == 0


def test_version_api_methods(app, db, pids):
    h1, h1v1, h1v2, h2, h2v1, c1, c1r1, c1r2, pid1 = \
        (pids[p] for p in ['h1', 'h1v1', 'h1v2', 'h2', 'h2v1',
                           'c1', 'c1r1', 'c1r2', 'pid1'])
    assert PIDVersionRelation.is_head(h1) is True
    assert PIDVersionRelation.is_head(h1v1) is False
    assert PIDVersionRelation.is_head(h1v2) is False
    assert PIDVersionRelation.is_head(h2) is True
    assert PIDVersionRelation.is_head(h2v1) is False

    # False for non-versioned PIDs and Collection concepts
    assert PIDVersionRelation.is_head(pid1) is False  # no Head PID
    assert PIDVersionRelation.is_head(c1) is False  # Collection PID
    assert PIDVersionRelation.is_head(c1r1) is False  # Collection resource
    assert PIDVersionRelation.is_head(c1r2) is False

    assert PIDVersionRelation.get_head(h1) == h1
    assert PIDVersionRelation.get_head(h1v1) == h1
    assert PIDVersionRelation.get_head(h1v2) == h1
    assert PIDVersionRelation.get_head(h2) == h2
    assert PIDVersionRelation.get_head(h2v1) == h2
    assert PIDVersionRelation.get_head(h2v1) == h2

    # Not supported for non-versioned PIDs and Collection concepts
    assert PIDVersionRelation.get_head(pid1) is None
    assert PIDVersionRelation.get_head(c1) is None
    assert PIDVersionRelation.get_head(c1r1) is None

    # Test 'is_version'/'get_all_versions'
    # True only for Version PIDs, False otherwise
    assert PIDVersionRelation.is_version(h1v1) is True
    assert PIDVersionRelation.is_version(h1v2) is True
    assert PIDVersionRelation.is_version(h1) is False
    assert PIDVersionRelation.is_version(c1) is False
    assert PIDVersionRelation.is_version(c1r1) is False
    assert PIDVersionRelation.is_version(c1r2) is False
    assert PIDVersionRelation.is_version(pid1) is False

    # Test 'get_all_versions'
    # Return all versions for Head and Version PID
    assert [h1v1, h1v2] == PIDVersionRelation.get_all_versions(h1)
    assert [h1v1, h1v2] == PIDVersionRelation.get_all_versions(h1v2)
    # Not supported for non-versioned PIDs and Collections
    assert PIDVersionRelation.get_all_versions(pid1) is None
    assert PIDVersionRelation.get_all_versions(c1) is None
    assert PIDVersionRelation.get_all_versions(c1r1) is None

    # Test 'is_latest'/'get_latest'
    assert PIDVersionRelation.get_latest(h1) == h1v2
    assert PIDVersionRelation.get_latest(h1v1) == h1v2
    assert PIDVersionRelation.get_latest(h1v2) == h1v2
    # Not supported for non-versioned PIDs and Collections
    assert PIDVersionRelation.get_latest(pid1) is None
    assert PIDVersionRelation.get_latest(c1) is None
    assert PIDVersionRelation.get_latest(c1r1) is None
    # NOTE: 'is_latest' is False for Head PID!
    assert PIDVersionRelation.is_latest(h1) is False
    assert PIDVersionRelation.is_latest(h1v1) is False
    assert PIDVersionRelation.is_latest(h1v2) is True
    # False for non-versioned PIDs and Collections
    assert PIDVersionRelation.is_latest(pid1) is False
    assert PIDVersionRelation.is_latest(c1) is False
    assert PIDVersionRelation.is_latest(c1r1) is False


def test_version_api_edit(app, db, pids):
    h1, h1v1, h1v2, h2, h2v1, c1, c1r1, c1r2, pid1 = \
        (pids[p] for p in ['h1', 'h1v1', 'h1v2', 'h2', 'h2v1',
                           'c1', 'c1r1', 'c1r2', 'pid1'])
    assert h1.get_redirect() == h1v2
    assert PIDVersionRelation.get_head(pid1) is None
    assert PIDVersionRelation.get_latest(h1) == h1v2
    assert PIDVersionRelation.get_latest(pid1) is None
    PIDVersionRelation.insert_version(h1, pid1, -1)
    assert h1.get_redirect() == pid1
    assert PIDVersionRelation.get_latest(h1) == pid1
    assert PIDVersionRelation.get_latest(pid1) == pid1
    assert PIDVersionRelation.get_head(pid1) == h1

    PIDVersionRelation.remove_version(pid1)
    assert h1.get_redirect() == h1v2
    assert PIDVersionRelation.get_latest(h1) == h1v2
    assert PIDVersionRelation.get_latest(pid1) is None
    assert PIDVersionRelation.get_head(pid1) is None

    PIDVersionRelation.insert_version(h1, pid1, 0)
    assert h1.get_redirect() == h1v2
    assert PIDVersionRelation.get_latest(h1) == h1v2
    assert PIDVersionRelation.get_latest(pid1) == h1v2
    assert PIDVersionRelation.get_head(pid1) == h1


def test_version_api_create_head(app, db, pids):
    """Test Head PID methods."""
    # Create an orphan PID
    pid = PersistentIdentifier.create('doi', 'barr.v1')

    assert PIDVersionRelation.is_head(pid) is False
    assert PIDVersionRelation.get_head(pid) is None

    # Add a Head PID to the orphan PID
    head_pid = PIDVersionRelation.create_head(pid, 'barr')
    # Check if Head PID redirects to the Version PID
    assert head_pid.get_redirect() == pid

    assert PIDVersionRelation.is_head(head_pid) is True
    assert PIDVersionRelation.is_head(pid) is False
    assert PIDVersionRelation.get_head(head_pid) == head_pid
    assert PIDVersionRelation.get_head(pid) == head_pid


def test_version_pid_methods(app, db):
    pid = PersistentIdentifier.create('doi', 'foobar.v1')
    assert PIDVersionRelation.is_version(pid) is False  # no Head PID
    assert PIDVersionRelation.is_latest(pid) is False  # no Head PID
    assert PIDVersionRelation.is_head(pid) is False

    head_pid = PIDVersionRelation.create_head(pid, 'foobar')

    assert PIDVersionRelation.is_head(pid) is False
    assert PIDVersionRelation.is_head(head_pid) is True
    assert PIDVersionRelation.is_version(pid) is True
    assert PIDVersionRelation.is_latest(pid) is True

    assert PIDVersionRelation.get_head(head_pid) == head_pid
    assert PIDVersionRelation.get_head(pid) == head_pid
