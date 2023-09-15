"""Add Environment.description

Revision ID: 8d63a091aff8
Revises: 48be4072fe58
Create Date: 2022-07-15 14:22:00.351131

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8d63a091aff8"
down_revision = "48be4072fe58"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("environment") as batch_op:
        batch_op.add_column(sa.Column("description", sa.UnicodeText(), nullable=True))


def downgrade():
    with op.batch_alter_table("environment") as batch_op:
        batch_op.drop_column("description")
