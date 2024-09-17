# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""lockfile spec

Revision ID: bf065abf375b
Revises: e17b4cc6e086
Create Date: 2024-03-02 09:21:02.519805

"""

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = "bf065abf375b"
down_revision = "e17b4cc6e086"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "specification",
        # https://github.com/sqlalchemy/sqlalchemy/issues/1403#issuecomment-1698365595
        sa.Column(
            "is_lockfile", sa.Boolean(), nullable=False, server_default=sa.sql.false()
        ),
    )


def downgrade():
    op.drop_column("specification", "is_lockfile")
