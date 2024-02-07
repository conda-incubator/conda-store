"""add worker

Revision ID: 0f7e23ff24ee
Revises: 771180018e1b
Create Date: 2023-12-13 21:01:45.546591

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0f7e23ff24ee"
down_revision = "771180018e1b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "worker",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("initialized", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("worker")
