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

"""PID relations indexers."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier

from .proxies import current_pidrelations
from .serializers.utils import serialize_relations


def index_relations(sender, json=None, record=None, index=None, **kwargs):
    """Add relations to the indexed record."""
    pid = PersistentIdentifier.query.filter(
        PersistentIdentifier.object_uuid == record.id,
        PersistentIdentifier.pid_type == current_pidrelations.primary_pid_type,
        ).one_or_none()
    if pid:
        relations = serialize_relations(pid)
        if relations:
            json['relations'] = relations
    # pids = (PersistentIdentifier.query
    #         .filter(PersistentIdentifier.object_uuid == record.id)
    #         .all())
    # relations = {}
    # if pids:
    #     for pid in pids:
    #         indexed = current_pidrelations.indexed_relations.get(pid.pid_type)
    #         if indexed:
    #             api_cls = indexed['api']
    #             api = api_cls(child=pid)
    #             if indexed.get('ordered', False):
    #                 relation = dict(
    #                     parent=api.parent.pid_value,
    #                     order=api.relation.index,
    #                     is_latest=api.is_last_child,
    #                     # siblings=[p.pid_value
    #                     #           for p in api.get_all_versions(pid)],
    #                     # FIXME: if siblings is ordered we don't need "last"
    #                     # and "order" fields. Otherwise we do. Also B2Share
    #                     # will probably not use "siblings". We need to be able
    #                     # to choose the fields we want to index.
    #                 )
    #             else:
    #                 relation = dict(
    #                     parent=api.parent.pid_value,
    #                 )
    #             relations[indexed['field']] = relation
    # if relations:
    #     json['relations'] = relations
    return json
