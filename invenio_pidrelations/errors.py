# SPDX-FileCopyrightText: 2017-2019 CERN.
# SPDX-License-Identifier: MIT

"""Errors for persistent identifiers."""

from __future__ import absolute_import, print_function


class PIDRelationError(Exception):
    """Base class for PIDRelations errors."""


class PIDRelationConsistencyError(PIDRelationError):
    """Base class for relation consistency errors."""
