"""add_cancelled_enum

Revision ID: 6d477abab205
Revises: cbe7aabdbc88
Create Date: 2023-02-01 16:37:31.252209

Solution to upgrade and downgrade refers to: https://stackoverflow.com/a/14845740
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6d477abab205"
down_revision = "cbe7aabdbc88"
branch_labels = None
depends_on = None

enum_name = "buildstatus"
tmp_enum_name = f"_{enum_name}"

old = ("QUEUED", "BUILDING", "COMPLETED", "FAILED")
new = ("QUEUED", "BUILDING", "COMPLETED", "CANCELLED", "FAILED")

old_type = sa.Enum(*old, name=enum_name)
new_type = sa.Enum(*new, name=enum_name)
tmp_type = sa.Enum(*new, name=tmp_enum_name)

table = "build"
column = "status"

alter_to_tmp = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {tmp_enum_name} USING {column}::text::{tmp_enum_name}"
alter_to_new = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {enum_name} USING {column}::text::{enum_name}"


def upgrade():
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute(alter_to_tmp)

    old_type.drop(op.get_bind(), checkfirst=False)

    new_type.create(op.get_bind())
    op.execute(alter_to_new)
    tmp_type.drop(op.get_bind(), checkfirst=False)


def downgrade():
    build = sa.sql.table("build", sa.Column("status", new_type, nullable=True))
    op.execute(
        build.update().where(build.c.status == "CANCELLED").values(status="FAILED")
    )

    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute(alter_to_tmp)

    new_type.drop(op.get_bind(), checkfirst=False)
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute(alter_to_new)
    tmp_type.drop(op.get_bind(), checkfirst=False)
