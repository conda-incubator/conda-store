"""add installer

Revision ID: 57cd11b949d5
Revises: 0f7e23ff24ee
Create Date: 2024-01-28 14:31:35.723505

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "57cd11b949d5"
down_revision = "0f7e23ff24ee"
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
    if not str(op.get_bind().engine.url).startswith("sqlite"):
        op.execute("DROP TYPE IF EXISTS buildartifacttype")


def downgrade():
    op.execute(
        "DELETE FROM build_artifact WHERE artifact_type = 'CONSTRUCTOR_INSTALLER'"
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
