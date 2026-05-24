# SPDX-FileCopyrightText: 2017-2019 CERN.
# SPDX-License-Identifier: MIT

"""Invenio module that adds PID relations to the Invenio-PIDStore module."""

from __future__ import absolute_import, print_function

from .ext import InvenioPIDRelations
from .version import __version__

__all__ = ("__version__", "InvenioPIDRelations")
