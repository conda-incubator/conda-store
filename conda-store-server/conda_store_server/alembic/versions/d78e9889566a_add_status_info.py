"""add status_info

Revision ID: d78e9889566a
Revises: b387747ca9b7
Create Date: 2023-11-07 12:25:04.416192

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d78e9889566a"
down_revision = "b387747ca9b7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("build", sa.Column("status_info", sa.UnicodeText(), nullable=True))


def downgrade():
    op.drop_column("build", "status_info")
