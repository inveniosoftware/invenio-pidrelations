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

"""Test search filter."""

from __future__ import absolute_import, print_function

from invenio_indexer.tasks import process_bulk_queue
from invenio_search import current_search_client
from invenio_pidstore.fetchers import recid_fetcher
from invenio_search.api import RecordsSearch, DefaultFilter

from invenio_pidrelations.search import LatestVersionFilter


class LatestVersionSearch(RecordsSearch):
    class Meta:
        """Test search class."""

        default_filter = LatestVersionFilter()


def test_search_filter(app, indexed_records, pids):
    """Check that LatestVersionFilter returns only latest versions."""
    search = LatestVersionSearch()
    query = search.query()
    result = query.execute()
    for hit in result.hits:
        assert hit.relation.version.is_latest is True
