"""adding a settings table

Revision ID: abd7248d5327
Revises: 16f65805dc8f
Create Date: 2023-05-11 16:38:12.210549

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "abd7248d5327"
down_revision = "16f65805dc8f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "setting",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("namespace_id", sa.Integer(), nullable=True),
        sa.Column("environment_id", sa.Integer(), nullable=True),
        sa.Column("key", sa.Unicode(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
    )

    with op.batch_alter_table(
        "setting",
        table_args=[
            sa.ForeignKeyConstraint(["namespace_id"], ["namespace.id"]),
            sa.ForeignKeyConstraint(["environment_id"], ["environment.id"]),
            sa.UniqueConstraint(
                "namespace_id", "environment_id", "key", name="_namespace_name_key_uc"
            ),
        ],
    ):
        pass


def downgrade():
    op.drop_table("setting")
