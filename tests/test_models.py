# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Model tests."""

from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from invenio_pidrelations.models import PIDRelation


def test_repr(db, version_relation):
    pid = PersistentIdentifier.create(
        'recid', 'barfoo', object_type='rec', status=PIDStatus.REGISTERED
    )
    pid_v1 = PersistentIdentifier.create(
        'recid', 'barfoo.v1', object_type='rec', status=PIDStatus.REGISTERED
    )
    pid_relation = PIDRelation.create(pid, pid_v1, version_relation.id, 0)

    assert (
        repr(pid_relation) ==
        "<PIDRelation: (recid:barfoo) -> (recid:barfoo.v1) (Type: 0, Idx: 0)>"
    )
