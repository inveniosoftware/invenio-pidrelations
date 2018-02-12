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

"""PIDRelation serialization utilities."""

from invenio_pidrelations.api import PIDRelation

from ..utils import resolve_relation_type_config


def serialize_relations(pid):
    """Serialize the relations for given PID."""
    data = {}
    relations = PIDRelation.get_child_relations(pid).all()
    parent_relation = PIDRelation.get_parent_relations(pid).first()
    if parent_relation:
        relations.append(parent_relation)

    for relation in relations:
        rel_cfg = resolve_relation_type_config(relation.relation_type)
        schema_class = rel_cfg.schema
        if schema_class is not None:
            schema = schema_class()
            schema.context['pid'] = pid
            result, errors = schema.dump(rel_cfg.api(pid))
            data.setdefault(rel_cfg.name, []).append(result)
    return data
