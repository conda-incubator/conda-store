# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""add user table

Revision ID: 98e16d86ffb0
Revises: bf065abf375b
Create Date: 2024-11-11 16:36:31.047525

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98e16d86ffb0'
down_revision = 'bf065abf375b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'userpermission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('environment_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('role', sa.Enum('NONE', 'VIEWER', 'EDITOR', 'ADMIN', name='role'), nullable=True),
        sa.ForeignKeyConstraint(['environment_id'], ['environment.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('userpermission')
    op.drop_table('user')
