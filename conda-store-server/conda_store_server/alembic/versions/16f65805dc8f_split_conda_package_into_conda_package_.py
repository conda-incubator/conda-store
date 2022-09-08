"""split conda_package into conda_package and conda_package_build

Revision ID: 16f65805dc8f
Revises: 5ad723de2abd
Create Date: 2022-08-24 12:01:48.461989

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "16f65805dc8f"
down_revision = "5ad723de2abd"
branch_labels = None
depends_on = None


def upgrade():

    # To migrate the data from conda_package, we'll use a temporary table.
    # We'll populate conda_package_tmp with the right data, then delete
    # conda_package and rename conda_package_tmp into conda_package
    op.create_table(
        "conda_package_tmp",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("channel_id", sa.Integer(), nullable=True),
        sa.Column("license", sa.Text(), nullable=True),
        sa.Column("license_family", sa.Unicode(length=64), nullable=True),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.Column("version", sa.Unicode(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # Creates table conda_package_build
    op.create_table(
        "conda_package_build",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=True),
        sa.Column("channel_id", sa.Integer(), nullable=True),
        sa.Column("build", sa.Unicode(length=64), nullable=False),
        sa.Column("build_number", sa.Integer(), nullable=False),
        sa.Column("constrains", sa.JSON(), nullable=True),
        sa.Column("depends", sa.JSON(), nullable=False),
        sa.Column("md5", sa.Unicode(length=255), nullable=False),
        sa.Column("sha256", sa.Unicode(length=64), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("subdir", sa.Unicode(length=64), nullable=True),
        sa.Column("timestamp", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["conda_package_tmp.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "package_id",
            "subdir",
            "build",
            "build_number",
            "sha256",
            name="_conda_package_build_uc",
        ),
    )

    # Creates index on build field
    op.create_index(
        op.f("ix_conda_package_build_build"),
        "conda_package_build",
        ["build"],
        unique=False,
    )

    # Creates table build_conda_package_build, which makes the link
    # between a conda-store build and its package builds
    op.create_table(
        "build_conda_package_build",
        sa.Column("build_id", sa.Integer(), nullable=False),
        sa.Column("conda_package_build_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["build.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["conda_package_build_id"], ["conda_package_build.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("build_id", "conda_package_build_id"),
    )

    op.create_table(
        "solve_conda_package_build",
        sa.Column("solve_id", sa.Integer(), nullable=False),
        sa.Column("conda_package_build_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conda_package_build_id"], ["conda_package_build.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["solve_id"], ["solve.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("solve_id", "conda_package_build_id"),
    )

    op.drop_constraint("_conda_package_build_uc", "conda_package_build", type_="unique")
    op.create_unique_constraint(
        "_conda_package_build_uc",
        "conda_package_build",
        ["channel_id", "package_id", "subdir", "build", "build_number", "sha256"],
    )
    op.create_foreign_key(
        "conda_package_build_channel_id_fkey", "conda_package_build", "conda_channel", ["channel_id"], ["id"]
    )

    # Migration starts here

    # Step 1 :
    # We insert in conda_package_tmp its right data.
    # We need to make a group by and use MAX() on the non-grouped fields, because
    # For a given (channel_id, name, version), the description or the license might be different.
    # Sometimes, the difference is just a dash in the license name : "Apache 2" -> "Apache-2"
    op.execute(
        """
    INSERT INTO conda_package_tmp (channel_id, license, license_family, name, version, summary, description)
        (
             SELECT channel_id, MAX(license), MAX(license_family), name, version, MAX(summary), MAX(description)
            FROM conda_package
            GROUP BY channel_id, name, version
        )

    """
    )

    
    # Step 2 : populate conda_package_build with the data from conda_package
    # We make a join on conda_package_tmp because we want the new package id (conda_package_tmp.id)
    # and not the former one (conda_package.id)
    op.execute(
        """
                INSERT INTO conda_package_build (md5, constrains, sha256, build_number, timestamp, size, build, subdir, depends, package_id, channel_id)
                SELECT DISTINCT ON(channel_id, subdir, build, build_number, sha256)
                    cp.md5,
                    cp.constrains,
                    cp.sha256,
                    cp.build_number,
                    cp.timestamp,
                    cp.size,
                    cp.build,
                    cp.subdir,
                    cp.depends,
                    tmp.id,
                    cp.channel_id
                FROM conda_package cp
                LEFT JOIN conda_package_tmp tmp
                    ON cp.channel_id = tmp.channel_id
                    AND cp.name = tmp.name
                    AND cp.version = tmp.version
                ORDER BY channel_id, subdir, build, build_number, sha256;
            """
    )
    

    # Step 3 : migrate the packages of builds, to point to conda_package_build data
    # instead of conda_package.
    op.execute(
        """
                INSERT INTO build_conda_package_build (build_id, conda_package_build_id)
                SELECT bcp.build_id, cpb.id
                FROM build_conda_package bcp
                LEFT JOIN conda_package cp ON bcp.conda_package_id = cp.id
                LEFT JOIN conda_package_build cpb ON cp.sha256 = cpb.sha256 AND cp.channel_id = cpb.channel_id;
            """
    )

    # Step 4 : same logic with the solves
    op.execute(
        """
                INSERT INTO solve_conda_package_build (solve_id, conda_package_build_id)
                SELECT scp.solve_id, cpb.id
                FROM solve_conda_package scp
                LEFT JOIN conda_package cp ON scp.conda_package_id = cp.id
                LEFT JOIN conda_package_build cpb ON cp.sha256 = cpb.sha256 AND cp.channel_id = cpb.channel_id;
            """
    )

    # Data are now migrated, let's clean up

    op.drop_table("solve_conda_package")
    op.drop_table("build_conda_package")
    op.drop_table("conda_package")
    op.rename_table("conda_package_tmp", "conda_package")

    op.create_foreign_key("build_specification_id_fkey", "build", "specification", ["specification_id"], ["id"])
    op.create_foreign_key("build_environment_id_fkey", "build", "environment", ["environment_id"], ["id"])
    op.create_foreign_key("build_artifact_build_id_fkey", "build_artifact", "build", ["build_id"], ["id"])
    op.create_unique_constraint(
        "_conda_package_uc", "conda_package", ["channel_id", "name", "version"]
    )

    op.create_index(
        op.f("ix_conda_package_channel_id"),
        "conda_package",
        ["channel_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conda_package_name"), "conda_package", ["name"], unique=False
    )
    op.create_index(
        op.f("ix_conda_package_version"), "conda_package", ["version"], unique=False
    )
    op.create_foreign_key(
        "conda_package_channel_id_fkey", "conda_package", "conda_channel", ["channel_id"], ["id"]
    )

    op.create_unique_constraint(
        "_namespace_name_uc", "environment", ["namespace_id", "name"]
    )
    op.create_foreign_key("environment_namespace_id_fkey", "environment", "namespace", ["namespace_id"], ["id"])
    op.create_foreign_key("environment_current_build_id_fkey", "environment", "build", ["current_build_id"], ["id"])
    op.create_foreign_key("solve_specification_id_fkey", "solve", "specification", ["specification_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    
    
    op.drop_constraint("solve_specification_id_fkey", "solve", type_="foreignkey")
    op.drop_constraint("environment_current_build_id_fkey", "environment", type_="foreignkey")
    op.drop_constraint("environment_namespace_id_fkey", "environment", type_="foreignkey")
    op.drop_constraint("_namespace_name_uc", "environment", type_="unique")


    
    # To migrate the data from conda_package and conda_package_build back into 
    # one table for both, we'll use a temporary table.
    # We'll populate conda_package_tmp with the right data, then delete
    # conda_package and conda_package_build, and then rename conda_package_tmp into conda_package
    
    op.create_table(
        "conda_package_tmp",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("channel_id", sa.Integer(), nullable=True),
        sa.Column("build", sa.Unicode(length=64), nullable=False),
        sa.Column("build_number", sa.Integer(), nullable=False),
        sa.Column("constrains", sa.JSON(), nullable=True),
        sa.Column("depends", sa.JSON(), nullable=False),
        sa.Column("license", sa.Text(), nullable=True),
        sa.Column("license_family", sa.Unicode(length=64), nullable=True),
        sa.Column("md5", sa.Unicode(length=255), nullable=False),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.Column("sha256", sa.Unicode(length=64), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("subdir", sa.Unicode(length=64), nullable=True),
        sa.Column("timestamp", sa.BigInteger(), nullable=True),
        sa.Column("version", sa.Unicode(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )

    with op.batch_alter_table(
        "conda_package",
        table_args=[
            sa.ForeignKeyConstraint(
                ["channel_id"],
                ["conda_channel.id"],
            ),
            sa.UniqueConstraint(
                "channel_id",
                "subdir",
                "name",
                "version",
                "build",
                "build_number",
                "sha256",
                name="_conda_package_uc",
            ),
        ],
    ):
        pass


    op.create_table(
        "build_conda_package",
        sa.Column("build_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "conda_package_id", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.PrimaryKeyConstraint(
            "build_id", "conda_package_id", name="build_conda_package_pkey"
        ),
    )
    op.create_table(
        "solve_conda_package",
        sa.Column("solve_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "conda_package_id", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.PrimaryKeyConstraint(
            "solve_id", "conda_package_id", name="solve_conda_package_pkey"
        ),
    )

    

    # Downgrade migration starts here

    # Step 1 :
    # We insert in conda_package_tmp its right data.
    
    op.execute(
        """INSERT INTO conda_package_tmp (channel_id, build,build_number,constrains,depends, license, license_family,
								md5, name, sha256, size,subdir, timestamp, version, summary, description)
            SELECT  cp.channel_id, 
                    cpb.build,
                    cpb.build_number,
                    cpb.constrains,
                    cpb.depends, 
                    cp.license, 
                    cp.license_family,
                    cpb.md5, 
                    cp.name, 
                    cpb.sha256,
                    cpb.size,
                    cpb.subdir, 
                    cpb.timestamp, 
                    cp.version, 
                    cp.summary, 
                    cp.description
            FROM conda_package cp
            LEFT JOIN conda_package_build cpb ON cpb.package_id = cp.id;
        """
    )

    # Step 2 : migrate the packages of builds, to point to conda_package_build data
    # instead of conda_package.
    op.execute(
        """
                INSERT INTO build_conda_package (build_id, conda_package_id) 
                SELECT bcpb.build_id,
                       cpt.id
                FROM build_conda_package_build bcpb
                LEFT JOIN conda_package_build cpb ON bcpb.conda_package_build_id = cpb.id
                LEFT JOIN conda_package_tmp cpt ON cpb.sha256 = cpt.sha256
                AND cpt.channel_id = cpb.channel_id;
            """
    )

    # Step 3 : same logic with the solves 
    op.execute(
        """
                INSERT INTO solve_conda_package (solve_id, conda_package_id)
                SELECT scpb.solve_id, cpt.id
                FROM solve_conda_package_build scpb
                LEFT JOIN conda_package_build cpb ON scpb.conda_package_build_id = cpb.id
                LEFT JOIN conda_package_tmp cpt ON cpb.sha256 = cpt.sha256
                AND cpt.channel_id = cpb.channel_id;

            """
    )


    op.drop_constraint("build_artifact_build_id_fkey", "build_artifact", type_="foreignkey")
    op.drop_constraint("build_environment_id_fkey", "build", type_="foreignkey")
    op.drop_constraint("build_specification_id_fkey", "build", type_="foreignkey")


    op.drop_table("solve_conda_package_build")
    op.drop_table("build_conda_package_build")
    op.drop_index(
        op.f("ix_conda_package_build_build"), table_name="conda_package_build"
    )
    op.drop_table("conda_package_build")
    op.drop_table("conda_package")
    op.rename_table("conda_package_tmp", "conda_package")

    # ### end Alembic commands ###
