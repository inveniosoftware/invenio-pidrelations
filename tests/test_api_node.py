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

import pytest
from invenio_pidstore.models import PIDStatus, PersistentIdentifier
from test_helpers import pid_to_fetched_recid

from invenio_pidrelations.api import PIDNode, PIDNodeOrdered

with_pid_and_fetched_pid = pytest.mark.parametrize("build_pid", [
    (lambda pid: pid),
    # test with a fetched PID
    (lambda pid: pid_to_fetched_recid(pid)),
])
"""Decorator used to test with real PersistentIdentifier and fetched PID."""


def create_pids(number):
    return [PersistentIdentifier.create(
        'recid', 'pid_value_{}'.format(p), object_type='rec',
        status=PIDStatus.REGISTERED) for p in range(number)]


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

    # inserting in the end
    ordered_parent_node.insert_child(child_pids[0], -1)
    version_pids[0]['children'].append(child_pids[0])
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # inserting in the beginning
    ordered_parent_node.insert_child(child_pids[1], 0)
    version_pids[0]['children'].insert(0, child_pids[1])
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # inserting in the middle
    ordered_parent_node.insert_child(child_pids[2], 3)
    version_pids[0]['children'].insert(3, child_pids[2])
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])


@with_pid_and_fetched_pid
def test_ordered_node_remove(db, version_relation, version_pids,
                             build_pid, recids):
    """Test PIDNode.remove_child."""
    parent_pid = build_pid(version_pids[0]['parent'])
    ordered_parent_node = PIDNodeOrdered(parent_pid,
                                         version_relation)
    # x-c-c-c-c
    # remove the first child
    ordered_parent_node.remove_child(version_pids[0]['children'][0])
    del version_pids[0]['children'][0]
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # c-c-c-x
    # remove the last child
    ordered_parent_node.remove_child(version_pids[0]['children'][-1])
    del version_pids[0]['children'][-1]
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])

    # c-x-c
    # remove the middle child
    ordered_parent_node.remove_child(version_pids[0]['children'][1])
    del version_pids[0]['children'][1]
    assert_children_indices(ordered_parent_node, version_pids[0]['children'])
