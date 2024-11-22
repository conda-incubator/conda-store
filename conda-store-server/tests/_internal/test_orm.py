# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import mock

import pytest

from conda_store_server import api
from conda_store_server._internal import orm


@pytest.fixture
def populated_db(db):
    """A database fixture populated with
    * 2 channels
    * 2 conda packages
    * 3 conda package builds
    """
    # create test channels
    api.create_conda_channel(db, "test-channel-1")
    api.create_conda_channel(db, "test-channel-2")
    db.commit()

    # create some sample conda_package's
    conda_package_records = [
        {
            "channel_id": 1,
            "name": "test-package-1",
            "version": "1.0.0",
            "license": "",
            "license_family": "",
            "summary": "",
            "description": "",
        },
        {
            "channel_id": 2,
            "name": "test-package-1",
            "version": "1.0.0",
            "license": "",
            "license_family": "",
            "summary": "",
            "description": "",
        },
    ]
    for conda_package_record in conda_package_records:
        api.create_conda_package(db, conda_package_record)
    db.commit()

    # create some conda_package_build's
    conda_package_builds = [
        (
            1,
            {
                "build": "py310h06a4308_0",
                "channel_id": 1,
                "build_number": 0,
                "sha256": "11f080b53b36c056dbd86ccd6dc56c40e3e70359f64279b1658bb69f91ae726f",
                "subdir": "linux-64",
                "constrains": "",
                "md5": "",
                "depends": "",
                "timestamp": "",
                "size": "",
            },
        ),
        (
            1,
            {
                "build": "py311h06a4308_0",
                "channel_id": 1,
                "build_number": 0,
                "sha256": "f0719ee6940402a1ea586921acfaf752fda977dbbba74407856a71ba7f6c4e4a",
                "subdir": "linux-64",
                "constrains": "",
                "md5": "",
                "depends": "",
                "timestamp": "",
                "size": "",
            },
        ),
        (
            1,
            {
                "build": "py38h06a4308_0",
                "channel_id": 1,
                "build_number": 0,
                "sha256": "39e39a23baebd0598c1b59ae0e82b5ffd6a3230325da4c331231d55cbcf13b3e",
                "subdir": "linux-64",
                "constrains": "",
                "md5": "",
                "depends": "",
                "timestamp": "",
                "size": "",
            },
        ),
    ]
    for cpb in conda_package_builds:
        conda_package_build = orm.CondaPackageBuild(
            package_id=cpb[0],
            **cpb[1],
        )
        db.add(conda_package_build)
    db.commit()

    return db


@pytest.fixture
def test_repodata():
    """Basic repodata for linux-64 subdir with 1 package"""
    return {
        "architectures": {
            "linux-64": {
                "packages": {
                    "test-package-1-0.1.0-py310_0.tar.bz2": {
                        "build": "py37_0",
                        "build_number": 0,
                        "depends": ["some-depends"],
                        "license": "BSD",
                        "md5": "a75683f8d9f5b58c19a8ec5d0b7f796e",
                        "name": "test-package-1",
                        "sha256": "1fe3c3f4250e51886838e8e0287e39029d601b9f493ea05c37a2630a9fe5810f",
                        "size": 3832,
                        "subdir": "linux-64",
                        "timestamp": 1530731681870,
                        "version": "0.1.0",
                    },
                }
            },
        }
    }


@pytest.fixture
def test_repodata_multiple_packages():
    """Basic repodata for linux-64 subdir with 2 builds for the same package"""
    return {
        "architectures": {
            "linux-64": {
                "packages": {
                    "test-package-1-1.0.0-py310_0.tar.bz2": {
                        "build": "py310_0",
                        "build_number": 0,
                        "depends": ["some-depends"],
                        "license": "BSD",
                        "md5": "a75683f8d9f5b58c19a8ec5d0b7f796e",
                        "name": "test-package-1",
                        "sha256": "1fe3c3f4250e51886838e8e0287e39029d601b9f493ea05c37a26something",
                        "size": 3832,
                        "subdir": "linux-64",
                        "timestamp": 1530731681870,
                        "version": "1.0.0",
                    },
                    "test-package-1-1.0.0-py37_0.tar.bz2": {
                        "build": "py37_0",
                        "build_number": 0,
                        "depends": ["some-depends"],
                        "license": "BSD",
                        "md5": "a75683f8d9f5b58c19a8ec5d0b7f796e",
                        "name": "test-package-1",
                        "sha256": "1fe3c3f4250e51886838e8e0287e39029d601b9f493ea05c37a26else",
                        "size": 3832,
                        "subdir": "linux-64",
                        "timestamp": 1530731681870,
                        "version": "1.0.0",
                    },
                }
            }
        }
    }


@mock.patch("conda_store_server._internal.conda_utils.download_repodata")
def test_update_packages_first_time(mock_repdata, db, test_repodata):
    # mock download_repodata to return static test repodata
    mock_repdata.return_value = test_repodata

    # create test channel
    channel = api.create_conda_channel(db, "test-channel-1")

    channel.update_packages(db, "linux-64")

    # ensure the package is added
    conda_packages = db.query(orm.CondaPackage).all()
    assert len(conda_packages) == 1

    conda_packages = db.query(orm.CondaPackageBuild).all()
    assert len(conda_packages) == 1


@mock.patch("conda_store_server._internal.conda_utils.download_repodata")
def test_update_packages_add_existing_pkg_new_version(
    mock_repdata, populated_db, test_repodata
):
    # mock download_repodata to return static test repodata
    mock_repdata.return_value = test_repodata

    # check state of db before updating packages
    count = (
        populated_db.query(orm.CondaPackage)
        .filter(orm.CondaPackage.channel_id == 1)
        .count()
    )
    assert count == 1
    count = populated_db.query(orm.CondaPackage).count()
    assert count == 2

    channel = (
        populated_db.query(orm.CondaChannel).filter(orm.CondaChannel.id == 1).first()
    )
    channel.update_packages(populated_db, "linux-64")

    # ensure the package is added
    count = (
        populated_db.query(orm.CondaPackage)
        .filter(orm.CondaPackage.channel_id == 1)
        .count()
    )
    assert count == 2
    count = populated_db.query(orm.CondaPackage).count()
    assert count == 3
    builds = (
        populated_db.query(orm.CondaPackageBuild)
        .filter(orm.CondaPackageBuild.channel_id == 1)
        .all()
    )
    assert len(builds) == 4
    for b in builds:
        assert b.package.channel_id == 1
    count = populated_db.query(orm.CondaPackageBuild).count()
    assert count == 4


@mock.patch("conda_store_server._internal.conda_utils.download_repodata")
def test_update_packages_multiple_subdirs(mock_repdata, populated_db):
    # mock download_repodata to return static test repodata
    repodata = {
        "architectures": {
            "win-64": {
                "packages": {
                    "_libgcc_mutex-1.0.0-py310_0.tar.bz2": {
                        "build": "py37_0",
                        "build_number": 0,
                        "depends": ["some-depends"],
                        "license": "BSD",
                        "md5": "a75683f8d9f5b58c19a8ec5d0b7f3sg5",
                        "name": "_libgcc_mutex",
                        "sha256": "1fe3c3f4250e51886838e8e0287e39029d601b9f493ea05c37a2630a9fe123s",
                        "size": 3832,
                        "subdir": "win-64",
                        "timestamp": 1530731681870,
                        "version": "1.0.0",
                    },
                },
            },
            "linux-64": {
                "packages": {
                    "_libgcc_mutex-1.0.0-py310_0.tar.bz2": {
                        "build": "py37_0",
                        "build_number": 0,
                        "depends": ["some-depends"],
                        "license": "BSD",
                        "md5": "a75683f8d9f5b58c19a8ec5d0b7f796e",
                        "name": "_libgcc_mutex",
                        "sha256": "1fe3c3f4250e51886838e8e0287e39029d601b9f493ea05c37a2630a9fe5810f",
                        "size": 3832,
                        "subdir": "linux-64",
                        "timestamp": 1530731681870,
                        "version": "1.0.0",
                    },
                }
            },
        }
    }
    mock_repdata.return_value = repodata

    # check state of db before updating packages
    count = (
        populated_db.query(orm.CondaPackage)
        .filter(orm.CondaPackage.channel_id == 1)
        .count()
    )
    assert count == 1

    channel = (
        populated_db.query(orm.CondaChannel).filter(orm.CondaChannel.id == 1).first()
    )
    channel.update_packages(populated_db)

    # ensure the packages are added
    count = (
        populated_db.query(orm.CondaPackage)
        .filter(orm.CondaPackage.channel_id == 1)
        .count()
    )
    assert count == 2
    builds = (
        populated_db.query(orm.CondaPackageBuild)
        .filter(orm.CondaPackageBuild.channel_id == 1)
        .all()
    )
    assert len(builds) == 5
    for b in builds:
        assert b.package.channel_id == 1


@mock.patch("conda_store_server._internal.conda_utils.download_repodata")
def test_update_packages_twice(mock_repdata, populated_db, test_repodata):
    # mock download_repodata to return static test repodata
    mock_repdata.return_value = test_repodata

    def check_packages():
        # ensure package is added
        conda_packages = (
            populated_db.query(orm.CondaPackage)
            .filter(orm.CondaPackage.channel_id == 1)
            .all()
        )
        assert len(conda_packages) == 2
        conda_packages = (
            populated_db.query(orm.CondaPackage)
            .filter(orm.CondaPackage.channel_id == 2)
            .all()
        )
        assert len(conda_packages) == 1
        conda_packages = (
            populated_db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.channel_id == 1)
            .all()
        )
        assert len(conda_packages) == 4
        conda_packages = (
            populated_db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.channel_id == 2)
            .all()
        )
        assert len(conda_packages) == 0

    channel = (
        populated_db.query(orm.CondaChannel).filter(orm.CondaChannel.id == 1).first()
    )

    # run update
    channel.update_packages(populated_db, "linux-64")

    # check packages
    check_packages()

    # run update again
    channel.update_packages(populated_db, "linux-64")

    # ensure packages stay the same
    check_packages


@mock.patch("conda_store_server._internal.conda_utils.download_repodata")
def test_update_packages_new_package_channel(mock_repdata, populated_db, test_repodata):
    # mock download_repodata to return static test repodata
    mock_repdata.return_value = test_repodata

    channel = (
        populated_db.query(orm.CondaChannel).filter(orm.CondaChannel.id == 2).first()
    )
    channel.update_packages(populated_db, "linux-64")

    # ensure the package is added
    count = (
        populated_db.query(orm.CondaPackage)
        .filter(orm.CondaPackage.channel_id == 2)
        .count()
    )
    assert count == 2
    builds = (
        populated_db.query(orm.CondaPackageBuild)
        .filter(orm.CondaPackageBuild.channel_id == 2)
        .all()
    )
    assert len(builds) == 1
    for b in builds:
        assert b.package.channel_id == 2
    count = populated_db.query(orm.CondaPackageBuild).count()
    assert count == 4


@mock.patch("conda_store_server._internal.conda_utils.download_repodata")
def test_update_packages_multiple_builds(
    mock_repdata, populated_db, test_repodata_multiple_packages
):
    # mock download_repodata to return static test repodata
    mock_repdata.return_value = test_repodata_multiple_packages

    count = populated_db.query(orm.CondaPackageBuild).count()
    assert count == 3

    channel = (
        populated_db.query(orm.CondaChannel).filter(orm.CondaChannel.id == 2).first()
    )
    channel.update_packages(populated_db, "linux-64")

    # ensure the package is not added conda packages
    count = populated_db.query(orm.CondaPackage).count()
    assert count == 2

    # ensure it is added to conda package builds
    count = populated_db.query(orm.CondaPackageBuild).count()
    assert count == 5
    builds = (
        populated_db.query(orm.CondaPackageBuild)
        .filter(orm.CondaPackageBuild.channel_id == 2)
        .all()
    )
    assert len(builds) == 2
    for b in builds:
        assert b.package.channel_id == 2


@mock.patch("conda_store_server._internal.conda_utils.download_repodata")
def test_update_packages_channel_consistency(
    mock_repdata, populated_db, test_repodata_multiple_packages
):
    mock_repdata.return_value = test_repodata_multiple_packages

    channel = (
        populated_db.query(orm.CondaChannel).filter(orm.CondaChannel.id == 2).first()
    )
    channel.update_packages(populated_db, "linux-64")

    # ensure the package builds end up with the correct channel
    builds = (
        populated_db.query(orm.CondaPackageBuild)
        .filter(orm.CondaPackageBuild.channel_id == 2)
        .all()
    )
    for b in builds:
        assert b.channel_id == 2
        assert b.package.channel_id == 2

    # again with another channel
    channel = (
        populated_db.query(orm.CondaChannel).filter(orm.CondaChannel.id == 1).first()
    )
    channel.update_packages(populated_db, "linux-64")

    # ensure the package builds end up with the correct channel
    builds = (
        populated_db.query(orm.CondaPackageBuild)
        .filter(orm.CondaPackageBuild.channel_id == 1)
        .all()
    )
    for b in builds:
        assert b.channel_id == 1
        assert b.package.channel_id == 1
