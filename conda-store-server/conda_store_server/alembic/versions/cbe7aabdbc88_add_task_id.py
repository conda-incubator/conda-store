"""add_task_id

Revision ID: cbe7aabdbc88
Revises: 16f65805dc8f
Create Date: 2023-01-31 17:36:28.685212

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cbe7aabdbc88"
down_revision = "16f65805dc8f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("build", sa.Column("task_id", sa.String(), nullable=True))


def downgrade():
    op.drop_column("build", "task_id")
