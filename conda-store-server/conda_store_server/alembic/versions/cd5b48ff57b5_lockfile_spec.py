"""lockfile spec

Revision ID: cd5b48ff57b5
Revises: 03c839888c82
Create Date: 2024-03-02 09:21:02.519805

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cd5b48ff57b5"
down_revision = "03c839888c82"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "specification",
        # https://github.com/sqlalchemy/sqlalchemy/issues/1403#issuecomment-1698365595
        sa.Column(
            "is_lockfile", sa.Boolean(), nullable=False, server_default=sa.sql.false()
        ),
    )


def downgrade():
    op.drop_column("specification", "is_lockfile")
