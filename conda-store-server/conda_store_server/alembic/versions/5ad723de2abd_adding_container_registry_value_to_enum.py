"""Adding CONTAINER_REGISTRY value to enum

Revision ID: 5ad723de2abd
Revises: 8d63a091aff8
Create Date: 2022-08-05 22:14:34.110642

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5ad723de2abd"
down_revision = "8d63a091aff8"
branch_labels = None
depends_on = None


def upgrade():
    # Custom migration for postgres
    if op.get_bind().engine.name == "postgresql":
        op.execute("ALTER TYPE buildartifacttype ADD VALUE 'CONTAINER_REGISTRY';")
        return

    # Default migration for all the other engines
    old_type = sa.Enum(
        "DIRECTORY",
        "LOCKFILE",
        "LOGS",
        "YAML",
        "CONDA_PACK",
        "DOCKER_BLOB",
        "DOCKER_MANIFEST",
        name="buildartifacttype",
    )

    new_type = sa.Enum(
        "DIRECTORY",
        "LOCKFILE",
        "LOGS",
        "YAML",
        "CONDA_PACK",
        "DOCKER_BLOB",
        "DOCKER_MANIFEST",
        "CONTAINER_REGISTRY",
        name="buildartifacttype",
    )

    with op.batch_alter_table("build_artifact") as batch_op:
        batch_op.alter_column("artifact_type", type_=new_type, existing_type=old_type)


def downgrade():
    # harmless to keep extra enum around
    pass
