"""add build_key_version

Revision ID: 30b37e725c32
Revises: d78e9889566a
Create Date: 2023-11-17 14:34:40.688865

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "30b37e725c32"
down_revision = "d78e9889566a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "build",
        sa.Column(
            "build_key_version", sa.Integer(), nullable=False, server_default="1"
        ),
    )


def downgrade():
    op.drop_column("build", "build_key_version")
