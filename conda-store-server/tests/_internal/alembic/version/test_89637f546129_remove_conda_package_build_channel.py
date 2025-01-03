# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from conda_store_server import api
from conda_store_server._internal import orm


def setup_bad_data_db(conda_store):
    """A database fixture populated with
    * 2 channels
    * 2 conda packages
    * 5 conda package builds
    """
    with conda_store.session_factory() as db:
        # create test channels
        api.create_conda_channel(db, "test-channel-1")
        api.create_conda_channel(db, "test-channel-2")
        db.commit()

        # create some sample conda_package's
        # For simplicity, the channel_id's match the id of the conda_package.
        # So, when checking that the package build entries have been reassembled
        # the right way, check that the package_id in the conda_package_build is
        # equal to what would have been the channel_id (before the migration is run)
        conda_package_records = [
            {
                "id": 1,
                "channel_id": 1,
                "name": "test-package-1",
                "version": "1.0.0",
            },
            {
                "id": 2,
                "channel_id": 2,
                "name": "test-package-1",
                "version": "1.0.0",
            },
        ]
        for cpb in conda_package_records:
            conda_package = orm.CondaPackage(**cpb)
            db.add(conda_package)
        db.commit()

        # create some conda_package_build's
        conda_package_builds = [
            {
                "id": 1,
                "build": "py310h06a4308_0",
                "package_id": 1,
                "build_number": 0,
                "sha256": "one",
                "subdir": "linux-64",
            },
            {
                "id": 2,
                "build": "py311h06a4308_0",
                "package_id": 1,
                "build_number": 0,
                "sha256": "two",
                "subdir": "linux-64",
            },
            {
                "id": 3,
                "build": "py38h06a4308_0",
                "package_id": 1,
                "build_number": 0,
                "sha256": "three",
                "subdir": "linux-64",
            },
            {
                "id": 4,
                "build": "py39h06a4308_0",
                "package_id": 2,
                "build_number": 0,
                "sha256": "four",
                "subdir": "linux-64",
            },
            {
                "id": 5,
                "build": "py310h06a4308_0",
                "package_id": 2,
                "build_number": 0,
                "sha256": "five",
                "subdir": "linux-64",
            },
        ]
        default_values = {
            "depends": "",
            "md5": "",
            "timestamp": 0,
            "constrains": "",
            "size": 0,
        }
        for cpb in conda_package_builds:
            conda_package = orm.CondaPackageBuild(**cpb, **default_values)
            db.add(conda_package)
        db.commit()

        # force in some channel data
        # conda_package_build 1 should have package_id 2 after migration
        db.execute(text("UPDATE conda_package_build SET channel_id=2 WHERE id=1"))
        # conda_package_build 2 should have package_id 1 after migration
        db.execute(text("UPDATE conda_package_build SET channel_id=1 WHERE id=2"))
        # conda_package_build 3 should have package_id 1 after migration
        db.execute(text("UPDATE conda_package_build SET channel_id=1 WHERE id=3"))
        # conda_package_build 4 should have package_id 2 after migration
        db.execute(text("UPDATE conda_package_build SET channel_id=2 WHERE id=4"))

        # don't set conda_package_build 5 channel_id as a test case
        # conda_package_build 5 package_id should be unchanged (2) after migration

        db.commit()


def test_remove_conda_package_build_channel_basic(
    conda_store, alembic_config, alembic_runner
):
    """Simply run the upgrade and downgrade for this migration"""
    # migrate all the way to the target revision
    alembic_runner.migrate_up_to("89637f546129")

    # try downgrading
    alembic_runner.migrate_down_one()

    # ensure the channel_id column exists, will error if channel_id column does not exist
    with conda_store.session_factory() as db:
        db.execute(text("SELECT channel_id from conda_package_build"))

    # try upgrading once more
    alembic_runner.migrate_up_one()

    # ensure the channel_id column exists, will error if channel_id column does not exist
    with conda_store.session_factory() as db:
        with pytest.raises(OperationalError):
            db.execute(text("SELECT channel_id from conda_package_build"))


def test_remove_conda_package_build_bad_data(
    conda_store, alembic_config, alembic_runner
):
    """Simply run the upgrade and downgrade for this migration"""
    # migrate all the way to the target revision
    alembic_runner.migrate_up_to("89637f546129")

    # try downgrading
    alembic_runner.migrate_down_one()

    # ensure the channel_id column exists, will error if channel_id column does not exist
    with conda_store.session_factory() as db:
        db.execute(text("SELECT channel_id from conda_package_build"))

    # seed db with data that has broken data
    setup_bad_data_db(conda_store)

    # try upgrading once more
    alembic_runner.migrate_up_one()

    # ensure the channel_id column exists, will error if channel_id column does not exist
    with conda_store.session_factory() as db:
        with pytest.raises(OperationalError):
            db.execute(text("SELECT channel_id from conda_package_build"))

    # ensure all packages builds have the right package associated
    with conda_store.session_factory() as db:
        build = (
            db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.id == 1)
            .first()
        )
        assert build.package_id == 2

        build = (
            db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.id == 2)
            .first()
        )
        assert build.package_id == 1

        build = (
            db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.id == 3)
            .first()
        )
        assert build.package_id == 1

        build = (
            db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.id == 4)
            .first()
        )
        assert build.package_id == 2

        build = (
            db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.id == 5)
            .first()
        )
        assert build.package_id == 2
