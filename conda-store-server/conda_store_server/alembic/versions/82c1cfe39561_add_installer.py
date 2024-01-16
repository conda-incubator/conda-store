"""add installer

Revision ID: 82c1cfe39561
Revises: 771180018e1b
Create Date: 2024-01-15 07:13:06.261592

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "82c1cfe39561"
down_revision = "771180018e1b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "build_artifact",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "artifact_type",
            existing_type=sa.VARCHAR(length=18),
            type_=sa.VARCHAR(length=21),
            existing_nullable=False,
        )


def downgrade():
    op.execute(
        'DELETE FROM build_artifact WHERE artifact_type = "CONSTRUCTOR_INSTALLER"'
    )
    with op.batch_alter_table(
        "build_artifact",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "artifact_type",
            existing_type=sa.VARCHAR(length=21),
            type_=sa.VARCHAR(length=18),
            existing_nullable=False,
        )
