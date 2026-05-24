# SPDX-FileCopyrightText: 2017-2019 CERN.
# SPDX-License-Identifier: MIT

"""Create pidrelations branch."""

import sqlalchemy as sa
from alembic import op

revision = "2216c32d7059"
down_revision = None
branch_labels = ("invenio_pidrelations",)
depends_on = "999c62899c20"  # invenio-pidstore create tables


def upgrade():
    """Upgrade database."""


def downgrade():
    """Downgrade database."""
