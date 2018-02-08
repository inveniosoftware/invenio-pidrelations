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

import pytest
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from invenio_pidrelations.contrib.versioning import PIDNodeVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.utils import resolve_relation_type_config
from invenio_pidrelations.errors import PIDRelationConsistencyError

from test_helpers import create_pids, filter_pids


def test_versioning_children(db, version_pids):
    """Test the children property of PIDNoneVersioning."""
    h1 = PIDNodeVersioning(version_pids[0]['parent'])
    assert h1.children.ordered('asc').all() == \
        filter_pids(version_pids[0]['children'], PIDStatus.REGISTERED)


def test_versioning_insert(db, version_pids):
    """Test PIDNodeVersioning.insert_child(...)."""
    new_pids = create_pids(3)
    h1 = PIDNodeVersioning(version_pids[0]['parent'])
    # insert as first child
    h1.insert_child(new_pids[0], 0)
    version_pids[0]['children'].insert(0, new_pids[0])
    assert h1.children.ordered('asc').all() == \
        filter_pids(version_pids[0]['children'], PIDStatus.REGISTERED)

    # insert as last child. This should insert just before the draft
    version_pids[0]['children'].insert(h1.index(h1.draft_child), new_pids[1])
    h1.insert_child(new_pids[1], -1)
    # Check that the parent redirects to the added PID
    assert(version_pids[0]['parent'].get_redirect() == new_pids[1])
    # Register the draft so that it appears in the children
    h1.draft_child.register()
    h1.update_redirect()
    assert h1.children.ordered('asc').all() == \
        filter_pids(version_pids[0]['children'], PIDStatus.REGISTERED)

    # insert again but without a draft child. It should be inserted at the end.
    version_pids[0]['children'].append(new_pids[2])
    h1.insert_child(new_pids[2], -1)
    assert h1.children.ordered('asc').all() == \
        filter_pids(version_pids[0]['children'], PIDStatus.REGISTERED)

    reserved_pid = create_pids(1, status=PIDStatus.RESERVED)[0]

    # Check the exception raised when trying to insert a RESERVED PID
    with pytest.raises(PIDRelationConsistencyError):
        h1.insert_child(reserved_pid)
