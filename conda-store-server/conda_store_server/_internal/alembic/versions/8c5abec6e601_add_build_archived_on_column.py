# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""add build.archived_on column

Revision ID: 8c5abec6e601
Revises: 89637f546129
Create Date: 2025-01-15 13:33:19.529794

"""
from alembic import op
from sqlalchemy import Column, DateTime

# revision identifiers, used by Alembic.
revision = '8c5abec6e601'
down_revision = '89637f546129'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'build',
        Column("archived_on", DateTime, default=None),
    )


def downgrade():
    op.drop_column('build', 'archived_on')
