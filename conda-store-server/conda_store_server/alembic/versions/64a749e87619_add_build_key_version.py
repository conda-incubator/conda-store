"""add build_key_version

Revision ID: 64a749e87619
Revises: b387747ca9b7
Create Date: 2023-11-05 00:59:57.132192

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "64a749e87619"
down_revision = "b387747ca9b7"
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
