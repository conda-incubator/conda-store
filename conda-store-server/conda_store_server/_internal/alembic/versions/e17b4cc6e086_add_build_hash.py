# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""add build hash

Revision ID: e17b4cc6e086
Revises: 03c839888c82
Create Date: 2024-03-26 04:39:24.275214

"""

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = "e17b4cc6e086"
down_revision = "03c839888c82"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("build", sa.Column("hash", sa.Unicode(length=32), nullable=True))


def downgrade():
    op.drop_column("build", "hash")
