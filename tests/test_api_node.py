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
from invenio_pidrelations.api import PIDNode
from invenio_pidstore.models import PIDStatus

from test_helpers import pid_to_fetched_recid


with_pid_and_fetched_pid = pytest.mark.parametrize("build_pid", [
    (lambda pid: pid),
    # test with a fetched PID
    (lambda pid: pid_to_fetched_recid(pid)),
])
"""Decorator used to test with real PersistentIdentifier and fetched PID."""


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
