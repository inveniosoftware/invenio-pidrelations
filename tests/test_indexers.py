# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Indexer tests."""

from unittest.mock import patch

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_records.api import Record
from test_helpers import compare_dictionaries

from invenio_pidrelations.contrib.versioning import PIDNodeVersioning
from invenio_pidrelations.indexers import index_relations, index_siblings


def test_index_relations(app, db):
    """Test the index_relations method."""

    data_v1 = {"body": "test_body", "title": "test_title"}
    data_v2 = {"body": "test_body2", "title": "test_title2"}

    # add first child to the relation
    rec_v1 = Record.create(data_v1)
    parent_pid = RecordIdProvider.create(
        object_type="rec", object_uuid=None, status=PIDStatus.REGISTERED
    ).pid
    data_v1["conceptrecid"] = parent_pid.pid_value
    provider = RecordIdProvider.create("rec", rec_v1.id)
    data_v1["recid"] = provider.pid.pid_value
    versioning = PIDNodeVersioning(pid=parent_pid)
    versioning.insert_child(child_pid=provider.pid)
    db.session.commit()
    output = index_relations(app, "recid", record=rec_v1)
    expected_output = {
        "relations": {
            "version": [
                {
                    "children": [{"pid_type": "recid", "pid_value": "2"}],
                    "index": 0,
                    "is_child": True,
                    "is_last": True,
                    "is_parent": False,
                    "next": None,
                    "parent": {"pid_type": "recid", "pid_value": "1"},
                    "previous": None,
                    "type": "version",
                }
            ]
        }
    }
    assert compare_dictionaries(output, expected_output)
    # add second child to the relation
    rec_v2 = Record.create(data_v2)
    data_v2["conceptrecid"] = parent_pid.pid_value
    provider_v2 = RecordIdProvider.create("rec", rec_v2.id)
    versioning.insert_child(child_pid=provider_v2.pid)
    db.session.commit()
    output = index_relations(app, "recid", record=rec_v2)
    expected_output = {
        "relations": {
            "version": [
                {
                    "children": [
                        {"pid_type": "recid", "pid_value": "2"},
                        {"pid_type": "recid", "pid_value": "3"},
                    ],
                    "index": 1,
                    "is_child": True,
                    "is_last": True,
                    "is_parent": False,
                    "next": None,
                    "parent": {"pid_type": "recid", "pid_value": "1"},
                    "previous": {"pid_type": "recid", "pid_value": "2"},
                    "type": "version",
                }
            ]
        }
    }
    assert compare_dictionaries(output, expected_output)


def test_index_siblings(app, db, version_pids):
    """Test the index_siblings method."""
    # Create a pid relation with 3 children
    data_v1 = {"body": "test_body", "title": "test_title"}
    data_v2 = {"body": "test_body2", "title": "test_title2"}
    data_v3 = {"body": "test_body3", "title": "test_title3"}
    rec_v1 = Record.create(data_v1)
    parent_pid = RecordIdProvider.create(
        object_type="rec", object_uuid=None, status=PIDStatus.REGISTERED
    ).pid
    data_v1["conceptrecid"] = parent_pid.pid_value
    provider = RecordIdProvider.create("rec", rec_v1.id)
    data_v1["recid"] = provider.pid.pid_value
    versioning = PIDNodeVersioning(pid=parent_pid)
    versioning.insert_child(child_pid=provider.pid)

    rec_v2 = Record.create(data_v2)
    data_v2["conceptrecid"] = parent_pid.pid_value
    provider_v2 = RecordIdProvider.create("rec", rec_v2.id)
    data_v2["recid"] = provider_v2.pid.pid_value
    versioning.insert_child(child_pid=provider_v2.pid)

    rec_v3 = Record.create(data_v3)
    data_v3["conceptrecid"] = parent_pid.pid_value
    provider_v3 = RecordIdProvider.create("rec", rec_v3.id)
    data_v3["recid"] = provider.pid.pid_value
    versioning.insert_child(child_pid=provider_v3.pid)
    db.session.commit()

    with patch("invenio_indexer.api.RecordIndexer.index_by_id") as mock:
        index_siblings(provider.pid, include_pid=True, eager=True, with_deposits=False)
        mock.assert_any_call(str(provider.pid.object_uuid))
        mock.assert_any_call(str(provider_v2.pid.object_uuid))
        mock.assert_any_call(str(provider_v3.pid.object_uuid))
