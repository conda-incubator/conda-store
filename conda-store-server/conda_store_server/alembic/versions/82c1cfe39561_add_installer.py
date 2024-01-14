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
        "build_artifact", schema=None, recreate="always"
    ) as batch_op:
        batch_op.alter_column(
            "artifact_type",
            existing_type=sa.VARCHAR(length=18),
            type_=sa.Enum(
                "DIRECTORY",
                "LOCKFILE",
                "LOGS",
                "YAML",
                "CONDA_PACK",
                "DOCKER_BLOB",
                "DOCKER_MANIFEST",
                "CONTAINER_REGISTRY",
                "CONSTRUCTOR_INSTALLER",
                name="buildartifacttype",
            ),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table(
        "build_artifact", schema=None, recreate="always"
    ) as batch_op:
        batch_op.alter_column(
            "artifact_type",
            existing_type=sa.Enum(
                "DIRECTORY",
                "LOCKFILE",
                "LOGS",
                "YAML",
                "CONDA_PACK",
                "DOCKER_BLOB",
                "DOCKER_MANIFEST",
                "CONTAINER_REGISTRY",
                "CONSTRUCTOR_INSTALLER",
                name="buildartifacttype",
            ),
            type_=sa.VARCHAR(length=18),
            existing_nullable=False,
        )
