"""add v2 role mappings

Revision ID: 771180018e1b
Revises: 30b37e725c32
Create Date: 2023-11-29 09:02:35.835664

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "771180018e1b"
down_revision = "30b37e725c32"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "namespace_role_mapping_v2",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("namespace_id", sa.Integer(), nullable=False),
        sa.Column("other_namespace_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.Unicode(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["namespace.id"],
        ),
        sa.ForeignKeyConstraint(
            ["other_namespace_id"],
            ["namespace.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("namespace_id", "other_namespace_id", name="_uc"),
    )


def downgrade():
    op.drop_table("namespace_role_mapping_v2")
