"""Adding CONTAINER_REGISTRY value to enum

Revision ID: 5ad723de2abd
Revises: 8d63a091aff8
Create Date: 2022-08-05 22:14:34.110642

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '5ad723de2abd'
down_revision = '8d63a091aff8'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE buildartifacttype ADD VALUE 'CONTAINER_REGISTRY'")


def downgrade():
    # harmless to keep extra enum around
    pass
