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

"""Records integration for PIDRelations."""

from functools import wraps

from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, \
    RecordIdentifier
from invenio_records_files.models import RecordsBuckets
from werkzeug.local import LocalProxy

from ..api import PIDConcept
from ..contrib.versioning import PIDVersioning
from ..proxies import current_pidrelations


def default_parent_minter(record_uuid, data, pid_type, object_type):
    """Basic RecordIdentifier-based minter for parent PIDs."""
    parent_id = RecordIdentifier.next()
    return PersistentIdentifier.create(
        pid_type=pid_type,
        pid_value=str(parent_id),
        object_type=object_type,
        status=PIDStatus.REGISTERED,
    )


def versioned_minter(pid_type='recid', object_type='rec', parent_minter=None):
    """Parameterized minter decorator for automatic versioning.

    This decorator can be applied to any minter function. in order to introduce
    record versioning through the `relations` metadata key.
    """
    parent_minter = parent_minter or default_parent_minter

    def decorator(child_minter):
        @wraps(child_minter)
        def wrapper(record_uuid=None, data=None):
            parent = (data.get('relations', {}).get('version', {})
                      .get('parent'))
            if not parent:
                # Not yet versioned, create parent PID
                parent_pid = parent_minter(record_uuid, data, pid_type,
                                           object_type)
                data['relations'] = {
                    'version': {'parent': parent_pid.pid_value}
                }
            else:
                parent_pid = PersistentIdentifier.get(
                    pid_type=pid_type, pid_value=parent)

            # Call the decorated minter to get the new PID
            pid = child_minter(record_uuid, data)

            versioning = PIDVersioning(parent=parent_pid)
            versioning.insert_child(child=pid)
            return pid
        return wrapper
    return decorator


class RecordDraft(object):
    """Record Draft relationship.

    Users of this class should make calls to `link` and `unlink` based on their
    specific use-cases. Typical scenario is that of creating a new Deposit
    which is linked to a not-yet published record PID (PID status is RESERVED).
    Linking these two makes it possible for creating new record versions and
    having the abiltiy to track their deposits.

    NOTE: This relation exists because usually newly created records are not
    immediately stored inside the database (they have no `RecordMetada`). This
    leads to having deposits that are hanging onto no actual record and only
    possess "soft" links to their records' PIDs through metadata.
    """

    class _RecordDraft(PIDConcept):
        """Internal class being used for API access."""

        def __init__(self, child=None, parent=None, relation=None):
            RECORD_DRAFT = current_pidrelations.relation_types['RECORD_DRAFT']
            self.relation_type = RECORD_DRAFT
            if relation is not None:
                assert relation.relation_type == RECORD_DRAFT
                return super(RecordDraft._RecordDraft, self).__init__(relation=relation)
            else:
                return super(RecordDraft._RecordDraft, self).__init__(
                    child=child, parent=parent, relation_type=RECORD_DRAFT,
                    relation=relation)

    @classmethod
    def link(cls, recid, depid):
        """Link a recid and depid."""
        return cls._RecordDraft(parent=recid).insert_child(depid)

    @classmethod
    def unlink(cls, recid, depid):
        """Unlink a recid and depid."""
        return cls._RecordDraft(parent=recid).remove_child(depid)

    @classmethod
    def get_draft(cls, recid):
        """Get the draft of a record."""
        return cls._RecordDraft(parent=recid).last_child

    @classmethod
    def get_recid(cls, depid):
        """Get the recid of a record."""
        return cls._RecordDraft(child=depid).parent


def clone_record_files(src_record, dst_record):
    """Create copy a record's files."""
    # NOTE `Bucket.snapshot` doesn't set `locked`
    snapshot = src_record.files.bucket.snapshot(lock=False)
    snapshot.locked = False

    RecordsBuckets.create(record=dst_record.model, bucket=snapshot)

    dst_record['_files'] = dst_record.files.dumps()
    dst_record['_buckets'] = {'deposit': str(snapshot.id)}


def index_siblings(pid, only_previous_version=False):
    """Send sibling records of the passed pid for indexing."""
    siblings = (
        PIDVersioning(child=pid)
        .children.filter(PersistentIdentifier.status == PIDStatus.REGISTERED)
        .all()
    )
    prev_ver = only_previous_version and siblings[-2:-2]
    if prev_ver:
        RecordIndexer().index_by_id(str(prev_ver.objec_uuid))
    else:
        RecordIndexer().bulk_index([str(s.object_uuid)
                                    for s in siblings if s != pid])
