# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-License-Identifier: MIT

"""Model tests."""

from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from invenio_pidrelations.models import PIDRelation


def test_repr(db, version_relation):
    pid = PersistentIdentifier.create(
        "recid", "barfoo", object_type="rec", status=PIDStatus.REGISTERED
    )
    pid_v1 = PersistentIdentifier.create(
        "recid", "barfoo.v1", object_type="rec", status=PIDStatus.REGISTERED
    )
    pid_relation = PIDRelation.create(pid, pid_v1, version_relation.id, 0)

    assert (
        repr(pid_relation)
        == "<PIDRelation: (recid:barfoo) -> (recid:barfoo.v1) (Type: 0, Idx: 0)>"
    )
