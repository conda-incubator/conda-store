"""role mapping

Revision ID: b387747ca9b7
Revises: abd7248d5327
Create Date: 2023-07-04 14:35:48.177574

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b387747ca9b7"
down_revision = "abd7248d5327"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "namespace_role_mapping",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("namespace_id", sa.Integer(), nullable=False),
        sa.Column("entity", sa.Unicode(length=255), nullable=False),
        sa.Column("role", sa.Unicode(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["namespace.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column(
        "namespace", sa.Column("role_mapping_metadata", sa.JSON(), nullable=True)
    )


def downgrade():
    op.drop_column("namespace", "role_mapping_metadata")
    op.drop_table("namespace_role_mapping")
