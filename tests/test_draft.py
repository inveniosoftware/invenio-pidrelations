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

"""PIDNodeDraft contribution module tests."""

from __future__ import absolute_import, print_function

import pytest
from invenio_pidstore.models import PersistentIdentifier

from invenio_pidrelations.contrib.draft import PIDNodeDraft
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.utils import resolve_relation_type_config
from invenio_pidrelations.errors import PIDRelationConsistencyError

from test_helpers import with_pid_and_fetched_pid, create_pids


@with_pid_and_fetched_pid
def test_record_draft(app, db, build_pid, recids):
    """Test RecordDraft API."""

    parent_pids = [PIDNodeDraft(pid) for pid in create_pids(2, 'parent')]
    draft_pids = create_pids(2, 'draft')

    # create a parent-draft relationship
    parent_pids[0].insert_child(draft_pids[0])

    assert parent_pids[0].children.all() == [draft_pids[0]]

    # try to create invalid additional parent-draft relationships
    with pytest.raises(PIDRelationConsistencyError):
        parent_pids[0].insert_child(draft_pids[1])
        parent_pids[1].insert_child(draft_pids[0])
