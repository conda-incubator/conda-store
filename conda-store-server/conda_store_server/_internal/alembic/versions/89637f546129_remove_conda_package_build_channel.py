# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""remove conda package build channel

Revision ID: 89637f546129
Revises: bf065abf375b
Create Date: 2024-12-04 13:09:25.562450

"""
from alembic import op
from sqlalchemy import Column, INTEGER, String, ForeignKey, table, select


# revision identifiers, used by Alembic.
revision = '89637f546129'
down_revision = 'bf065abf375b'
branch_labels = None
depends_on = None

# Due to the issue fixed in https://github.com/conda-incubator/conda-store/pull/961
# many conda_package_build entries have the wrong package entry (but the right channel).
# Because the packages are duplicated, we can not recreate the _conda_package_build_uc
# constraint without the channel_id.
# So, this function will go thru each conda_package_build and re-associate it with the
# correct conda_package based on the channel id.
def fix_misrepresented_packages(conn):
    # conda_packages is a hash of channel-id_name_version to conda_package id
    conda_packages = {}

    # dummy tables to run queries against
    conda_package_build_table = table(
        "conda_package_build",
        Column("id", INTEGER),
        Column("channel_id", INTEGER),
        Column("package_id", INTEGER, ForeignKey("conda_package.id")),
    )
    conda_package_table = table(
        "conda_package",
        Column("id", INTEGER),
        Column("channel_id", INTEGER),
        Column("name", String),
        Column("version", String),
    )

    def get_conda_package_id(conn, channel_id, name, version):
        hashed_name = f"{channel_id}-{name}-{version}"

        # if package exists in the conda_packages dict, return it
        if hashed_name in conda_packages:
            return conda_packages[hashed_name]

        # if not, then query the db for the package
        package = conn.execute(
            select(conda_package_table).where(
                conda_package_table.c.channel_id == channel_id,
                conda_package_table.c.name == name,
                conda_package_table.c.version == version,
            )
        ).first()

        # save the package into the conda_packages dict
        conda_packages[hashed_name] = package.id
        return package.id

    for row in conn.execute(
        select(
            conda_package_build_table.c.id,
            conda_package_build_table.c.package_id,
            conda_package_build_table.c.channel_id,
            conda_package_table.c.name,
            conda_package_table.c.version
        ).join(
            conda_package_build_table,
            conda_package_build_table.c.package_id == conda_package_table.c.id
        )
    ):
        # the channel_id might already be empty
        if row[2] is None:
            continue

        package_id = get_conda_package_id(conn, row[2], row[3], row[4])
        # if found package id does not match the found package id, we'll need to updated it
        if package_id != row[1]:
            update_package_query = conda_package_build_table.update().where(
                conda_package_build_table.c.id == op.inline_literal(row[0])
            ).values(
                {"package_id": op.inline_literal(package_id)}
            )
            conn.execute(update_package_query)
            conn.commit()

def upgrade():
    bind = op.get_bind()

    # So, go thru each conda_package_build and re-associate it with the correct conda_package
    # based on the channel id.
    fix_misrepresented_packages(bind)

    with op.batch_alter_table("conda_package_build") as batch_op:
        # remove channel column from constraints
        batch_op.drop_constraint(
            "_conda_package_build_uc",
        )

        # re-add the constraint without the channel column
        batch_op.create_unique_constraint(
            "_conda_package_build_uc",
            [
                "package_id",
                "subdir",
                "build",
                "build_number",
                "sha256",
            ],
        )

        # remove channel column
        batch_op.drop_column(
            "channel_id",
        )


def downgrade():
    with op.batch_alter_table("conda_package_build") as batch_op:
        # remove channel column from constraints
        batch_op.drop_constraint(
            constraint_name="_conda_package_build_uc",
        )

        # add channel column
        batch_op.add_column(
            Column("channel_id", INTEGER)
        )

        batch_op.create_foreign_key("fk_channel_id", "conda_channel", ["channel_id"], ["id"])

        # re-add the constraint with the channel column
        batch_op.create_unique_constraint(
            constraint_name="_conda_package_build_uc",
            columns=[
                "channel_id",
                "package_id",
                "subdir",
                "build",
                "build_number",
                "sha256",
            ],
        )
