# SPDX-FileCopyrightText: 2017-2019 CERN.
# SPDX-License-Identifier: MIT

"""Proxy objects for easier access to application objects."""

from flask import current_app
from werkzeug.local import LocalProxy

current_pidrelations = LocalProxy(
    lambda: current_app.extensions["invenio-pidrelations"]
)
