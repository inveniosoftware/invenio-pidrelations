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

"""Records contribution module tests."""

from __future__ import absolute_import, print_function

import pytest

from invenio_pidstore.models import PersistentIdentifier

from invenio_pidrelations.contrib.records import RecordDraft
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.utils import resolve_relation_type_config


def test_record_draft(app, db):
    """Test RecordDraft API."""

    assert PersistentIdentifier.query.count() == 0
    assert PIDRelation.query.count() == 0

    d1 = PersistentIdentifier.create('depid', '1', object_type='rec')
    r1 = PersistentIdentifier.create('recid', '1', object_type='rec')
    assert PersistentIdentifier.query.count() == 2

    RecordDraft.link(recid=r1, depid=d1)
    assert PIDRelation.query.count() == 1

    pr = PIDRelation.query.one()
    RECORD_DRAFT = resolve_relation_type_config('record_draft').id
    assert pr.relation_type == RECORD_DRAFT
    assert pr.index is None
    assert pr.parent == r1
    assert pr.child == d1

    d2 = PersistentIdentifier.create('depid', '2', object_type='rec')
    r2 = PersistentIdentifier.create('recid', '2', object_type='rec')

    with pytest.raises(Exception) as excinfo:
        RecordDraft.link(recid=r1, depid=d2)
    assert 'already has a depid as a draft' in str(excinfo.value)

    with pytest.raises(Exception) as excinfo:
        RecordDraft.link(recid=r2, depid=d1)
    assert 'already is a draft of a recid' in str(excinfo.value)


