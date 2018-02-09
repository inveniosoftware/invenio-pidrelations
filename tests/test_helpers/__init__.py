# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017, 2018 CERN.
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

"""Test helpers."""

import pytest

from invenio_pidstore.models import PIDStatus, PersistentIdentifier
from invenio_pidstore.fetchers import FetchedPID
from invenio_pidstore.providers.recordid import RecordIdProvider


def pid_to_fetched_recid(pid):
    """Build a fetched recid from a PersistentIdentifier."""
    return FetchedPID(
        provider=RecordIdProvider,
        pid_type=RecordIdProvider.pid_type,
        pid_value=pid.pid_value,
    )


with_pid_and_fetched_pid = pytest.mark.parametrize("build_pid", [
    (lambda pid: pid),
    # test with a fetched PID
    (lambda pid: pid_to_fetched_recid(pid)),
])
"""Decorator used to test with real PersistentIdentifier and fetched PID."""


def create_pids(number, prefix='', status=PIDStatus.REGISTERED):
    """Create a give'n number of PIDs.

    :param number: number of PIDs to create.
    """
    return [PersistentIdentifier.create(
        'recid', '{0}_pid_value_{1}_{2}'.format(prefix, status, p),
        object_type='rec', status=status) for p in range(number)]


def filter_pids(pids, status):
    """Filter PIDs based on their status."""
    return [p for p in pids if p.status == status]
