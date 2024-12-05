# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""remove conda package build channel

Revision ID: 89637f546129
Revises: bf065abf375b
Create Date: 2024-12-04 13:09:25.562450

"""
from alembic import op, context
from sqlalchemy import Column, INTEGER, String, ForeignKey, table, select, engine_from_config, pool

# revision identifiers, used by Alembic.
revision = '89637f546129'
down_revision = 'bf065abf375b'
branch_labels = None
depends_on = None


# This function will go thru all the conda_package_build entries and ensure
# that the right package_id is associated with it
def fix_misrepresented_packages(conn):
    # conda_packages is a hash of channel-id_name_version to conda_package id
    conda_packages = {}

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
    target_table = "conda_package_build"
    bind = op.get_bind()

    # Due to the issue fixed in https://github.com/conda-incubator/conda-store/pull/961
    # many conda_package_build entries have the wrong package entry (but the right channel).
    # Because the packages are duplicated, we can not recreate the _conda_package_build_uc
    # constraint without the channel_id. 
    # So, go thru each conda_package_build and re-associate it with the correct conda_package
    # based on the channel id.
    fix_misrepresented_packages(bind)

    # remove channel column from constraints
    op.drop_constraint(
        constraint_name="_conda_package_build_uc",
        table_name=target_table,
    )

    # re-add the constraint without the channel column
    op.create_unique_constraint(
        constraint_name="_conda_package_build_uc",
        table_name=target_table,
        columns=[ 
            "package_id",
            "subdir",
            "build",
            "build_number",
            "sha256",
        ],
    )

    # remove channel column
    op.drop_column(
        target_table, 
        "channel_id",
        mssql_drop_foreign_key=True,
    )


def downgrade():
    target_table = "conda_package_build"

    # remove channel column from constraints
    op.drop_constraint(
        constraint_name="_conda_package_build_uc",
        table_name=target_table,
    )

    # add channel column
    op.add_column(
        target_table,
        Column("channel_id", INTEGER, ForeignKey("conda_channel.id"))
    )

    # re-add the constraint with the channel column
    op.create_unique_constraint(
        constraint_name="_conda_package_build_uc",
        table_name=target_table,
        columns=[ 
            "channel_id",
            "package_id",
            "subdir",
            "build",
            "build_number",
            "sha256",
        ],
    )
