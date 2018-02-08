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

"""api PIDNode tests."""

import os
import sys

import pytest
from invenio_pidstore.models import PIDStatus, PersistentIdentifier
from test_helpers import with_pid_and_fetched_pid, create_pids

from invenio_pidrelations.api import PIDNode, PIDNodeOrdered
from invenio_pidrelations.errors import PIDRelationConsistencyError


@with_pid_and_fetched_pid
def test_node_children(db, version_relation, version_pids, build_pid):
    """Test PIDNode.children()."""
    parent_node = PIDNode(build_pid(version_pids[0]['parent']),
                          version_relation)
    assert parent_node.children.ordered('asc').all() == \
        version_pids[0]['children']

    child_node = PIDNode(build_pid(version_pids[0]['children'][0]),
                         version_relation)
    assert child_node.children.ordered('asc').all() == []


@with_pid_and_fetched_pid
def test_node_is_parent(db, version_relation, version_pids, build_pid):
    """Test PIDNode.is_parent."""
    parent_node = PIDNode(build_pid(version_pids[0]['parent']),
                          version_relation)
    assert parent_node.is_parent

    child_node = PIDNode(build_pid(version_pids[0]['children'][0]),
                         version_relation)
    assert not child_node.is_parent


@with_pid_and_fetched_pid
def test_node_is_child(db, version_relation, version_pids, build_pid):
    """Test PIDNode.is_child."""
    parent_node = PIDNode(build_pid(version_pids[0]['parent']),
                          version_relation)
    assert not parent_node.is_child

    child_node = PIDNode(build_pid(version_pids[0]['children'][0]),
                         version_relation)
    assert child_node.is_child


@with_pid_and_fetched_pid
def test_node_insert_child(db, version_relation, version_pids, build_pid,
                           recids):
    """Test PIDNode.insert_child."""
    parent_pid = build_pid(version_pids[0]['parent'])
    parent_node = PIDNode(parent_pid,
                          version_relation)
    child_pid = build_pid(recids[str(PIDStatus.REGISTERED)])
    child_node = PIDNode(child_pid,
                         version_relation)
    assert not child_node.is_child

    parent_node.insert_child(child_pid)
    assert child_node.is_child
    assert child_node.parents.all() == [version_pids[0]['parent']]


@with_pid_and_fetched_pid
def test_node_remove_child(db, version_relation, version_pids, build_pid,
                           recids):
    """Test PIDNode.remove_child."""
    parent_pid = build_pid(version_pids[0]['parent'])
    parent_node = PIDNode(parent_pid,
                          version_relation)
    child_node = PIDNode(build_pid(version_pids[0]['children'][0]),
                         version_relation)
    parent_node.remove_child(version_pids[0]['children'][0])
    assert not child_node.is_child


@with_pid_and_fetched_pid
def test_ordered_node_index(db, version_relation,
                            version_pids, build_pid, recids):
    """Test the PIDNodeOrdered index method."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid, version_relation)

    for idx, child_pid in enumerate(version_pids[0]['children']):
        assert ordered_parent_node.index(child_pid) == idx

    child_pid = build_pid(recids[str(PIDStatus.REGISTERED)])
    ordered_parent_node.insert_child(child_pid)
    assert ordered_parent_node.index(child_pid) == 5


@with_pid_and_fetched_pid
def test_ordered_node_last_child(db, version_relation,
                                 version_pids, build_pid, recids):
    """Test the PIDNodeOrdered last_child method."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid, version_relation)
    assert ordered_parent_node.last_child == version_pids[0]['children'][-1]


@with_pid_and_fetched_pid
def test_ordered_node_next_child(db, version_relation, version_pids,
                                 build_pid, recids):
    """Test the PIDNodeOrdered next_child method."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid, version_relation)
    assert ordered_parent_node.next_child(version_pids[0]['children'][0]) == \
        version_pids[0]['children'][1]
    # Check that the next child can be retrieved if there is a "hole" in the
    # sequence of indices.
    ordered_parent_node.remove_child(version_pids[0]['children'][1],
                                     reorder=False)
    del version_pids[0]['children'][1]
    assert ordered_parent_node.next_child(version_pids[0]['children'][0]) == \
        version_pids[0]['children'][1]
    # Check that next_child returns None if there is no next child.
    assert ordered_parent_node.next_child(version_pids[0]['children'][-1]) \
        is None


@with_pid_and_fetched_pid
def test_ordered_node_previous_child(db, version_relation, version_pids,
                                     build_pid, recids):
    """Test the PIDNodeOrdered previous_child method."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid, version_relation)
    assert ordered_parent_node.previous_child(
        version_pids[0]['children'][-1]
    ) == version_pids[0]['children'][-2]
    # Check that the previous child can be retrieved if there is a "hole" in
    # the sequence of indices.
    ordered_parent_node.remove_child(version_pids[0]['children'][-2],
                                     reorder=False)
    del version_pids[0]['children'][-2]
    assert ordered_parent_node.previous_child(
        version_pids[0]['children'][-1]
    ) == version_pids[0]['children'][-2]
    # Check that previous_child returns None if there is no previous child.
    assert ordered_parent_node.previous_child(version_pids[0]['children'][0]) \
        is None


@with_pid_and_fetched_pid
def test_ordered_node_is_last_child(db, version_relation,
                                    version_pids, build_pid, recids):
    """Test the PIDNodeOrdered is_last_child method."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid, version_relation)
    assert ordered_parent_node.is_last_child(
        version_pids[0]['children'][-1])


def assert_children_indices(ordered_parent, children):
    """Check the indices of the list of children of a PIDNodeOrdered."""
    assert len(ordered_parent.children.all()) == len(children)
    for idx, child_pid in enumerate(children):
        assert ordered_parent.index(child_pid) == idx


@with_pid_and_fetched_pid
def test_ordered_node_insert(db, version_relation, version_pids,
                             build_pid, recids):
    """Test the PIDNodeOrdered insert method."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid, version_relation)
    child_pids = create_pids(3)

    # c-c-c-c-c-x
    # inserting in the end
    ordered_parent_node.insert_child(child_pids[0], -1)
    version_pids[0]['children'].append(child_pids[0])
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # x-c-c-c-c-c-c
    # inserting in the beginning
    ordered_parent_node.insert_child(child_pids[1], 0)
    version_pids[0]['children'].insert(0, child_pids[1])
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # c-c-c-x-c-c-c-c
    # inserting in the middle
    ordered_parent_node.insert_child(child_pids[2], 3)
    version_pids[0]['children'].insert(3, child_pids[2])
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])


@with_pid_and_fetched_pid
def test_ordered_node_remove_with_reorder(db, version_relation, version_pids,
                                          build_pid, recids):
    """Test PIDNode.remove_child."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid,
                                         version_relation)
    # x-c-c-c-c
    # remove the first child
    ordered_parent_node.remove_child(version_pids[0]['children'][0],
                                     reorder=True)
    del version_pids[0]['children'][0]
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # c-c-c-x
    # remove the last child
    ordered_parent_node.remove_child(version_pids[0]['children'][-1],
                                     reorder=True)
    del version_pids[0]['children'][-1]
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # c-x-c
    # remove the middle child
    ordered_parent_node.remove_child(version_pids[0]['children'][1],
                                     reorder=True)
    del version_pids[0]['children'][1]
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])


@with_pid_and_fetched_pid
def test_ordered_node_remove_without_reorder(db, version_relation,
                                             version_pids, build_pid, recids):
    """Test PIDNode.remove_child."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid,
                                         version_relation)

    # c-c-c-c-x
    # remove the last child
    ordered_parent_node.remove_child(version_pids[0]['children'][-1],
                                     reorder=False)
    del version_pids[0]['children'][-1]
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # x-c-c-c
    # remove the first child
    ordered_parent_node.remove_child(version_pids[0]['children'][0],
                                     reorder=False)
    del version_pids[0]['children'][0]
    assert len(ordered_parent_node.children.all()) == \
        len(version_pids[0]['children'])
    for idx, child_pid in enumerate(version_pids[0]['children']):
        assert ordered_parent_node.index(child_pid) == idx + 1

    # c-x-c
    # remove the middle child
    ordered_parent_node.remove_child(version_pids[0]['children'][1],
                                     reorder=False)
    del version_pids[0]['children'][1]
    assert len(ordered_parent_node.children.all()) == \
        len(version_pids[0]['children'])
    expected = [1, 3]
    for idx, child_pid in enumerate(version_pids[0]['children']):
        assert ordered_parent_node.index(child_pid) == expected[idx]


@with_pid_and_fetched_pid
def test_node_max_parents(db, version_relation, version_pids,
                          build_pid, recids):
    """Test the PIDNode max parents attribute."""
    parent_pid_1 = build_pid(version_pids[0]['parent'])
    parent_pid_2 = build_pid(version_pids[1]['parent'])
    ordered_parent_node_1 = PIDNode(parent_pid_1,
                                    version_relation, max_parents=1)
    ordered_parent_node_2 = PIDNode(parent_pid_2,
                                    version_relation, max_parents=1)
    child_pids = create_pids(1)

    ordered_parent_node_1.insert_child(child_pids[0])
    with pytest.raises(PIDRelationConsistencyError):
        ordered_parent_node_2.insert_child(child_pids[0])


@with_pid_and_fetched_pid
def test_node_max_children(db, version_relation, version_pids,
                           build_pid, recids):
    """Test the PIDNode max children attribute."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = \
        PIDNode(parent_pid,
                version_relation,
                max_children=len(version_pids[0]['children']))
    child_pids = create_pids(1)

    with pytest.raises(PIDRelationConsistencyError):
        ordered_parent_node.insert_child(child_pids[0])
