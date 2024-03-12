"""add canceled status

Revision ID: 03c839888c82
Revises: 57cd11b949d5
Create Date: 2024-01-29 03:56:36.889909

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "03c839888c82"
down_revision = "57cd11b949d5"
branch_labels = None
depends_on = None


# Migrating from/to VARCHAR having the same length might look strange, but it
# serves a purpose. This will be a no-op in SQLite because it represents Python
# enums as VARCHAR, but it will convert the enum in PostgreSQL to VARCHAR. The
# old type is set to VARCHAR here because you can cast an enum to VARCHAR, which
# is needed for the migration to work. In the end, both DBs will use VARCHAR to
# represent the Python enum, which makes it easier to support both DBs at the
# same time.
def upgrade():
    with op.batch_alter_table(
        "build",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.VARCHAR(length=9),
            type_=sa.VARCHAR(length=9),
            existing_nullable=False,
        )
    if not str(op.get_bind().engine.url).startswith("sqlite"):
        op.execute("DROP TYPE IF EXISTS buildstatus")


def downgrade():
    # There are foreign key constraints linking build ids to other tables. So
    # just mark the builds as failed, which was the status previously used for
    # canceled builds
    op.execute("UPDATE build SET status = 'FAILED' WHERE status = 'CANCELED'")
