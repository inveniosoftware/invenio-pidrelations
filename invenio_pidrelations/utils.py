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

"""PID relations utility functions."""

from __future__ import absolute_import, print_function

import six
from flask import current_app
from werkzeug.utils import import_string


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, six.string_types):
        return import_string(value)
    elif value:
        return value
    return default


def resolve_relation_type_config(value):
    """Resolve the relation type to config object.

    Resolve relation type from string (e.g.:  serialization) or int (db value)
    to the full config object.
    """
    relation_types = current_app.config['PIDRELATIONS_RELATION_TYPES']
    if isinstance(value, six.string_types):
        obj = next(rt for rt in relation_types if rt.name == value)
    elif isinstance(value, int):
        obj = next(rt for rt in relation_types if rt.id == value)
    else:
        raise ValueError("Provided value '{0}' does not resolve to any of the "
                         "configured relation types.")
    api_class = obj_or_import_string(obj.api)
    schema_class = obj_or_import_string(obj.schema)
    return obj.__class__(obj.id, obj.name, obj.label, api_class, schema_class)
