# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from conda_store_server import api
from conda_store_server._internal import schema
from conda_store_server._internal.worker import build


def test_build_started(db, seed_conda_store):
    test_build = api.get_build(db, build_id=4)
    assert test_build.status != schema.BuildStatus.BUILDING
    build.set_build_started(db, test_build)
    test_build = api.get_build(db, build_id=4)
    assert test_build.status == schema.BuildStatus.BUILDING


def test_build_failed(db, seed_conda_store):
    test_build = api.get_build(db, build_id=4)
    assert test_build.status != schema.BuildStatus.FAILED
    build.set_build_failed(db, test_build)
    test_build = api.get_build(db, build_id=4)
    assert test_build.status == schema.BuildStatus.FAILED


def test_build_canceled(db, seed_conda_store):
    test_build = api.get_build(db, build_id=4)
    assert test_build.status != schema.BuildStatus.CANCELED
    build.set_build_canceled(db, test_build)
    test_build = api.get_build(db, build_id=4)
    assert test_build.status == schema.BuildStatus.CANCELED


def test_build_completed(db, conda_store, seed_conda_store):
    test_build = api.get_build(db, build_id=2)
    assert test_build.status != schema.BuildStatus.COMPLETED
    build.set_build_completed(db, conda_store, test_build)
    test_build = api.get_build(db, build_id=2)
    assert test_build.status == schema.BuildStatus.COMPLETED
    assert test_build.environment.current_build == test_build
    build_artifact = api.get_build_artifact(
        db, 2, str(test_build.build_path(conda_store))
    )
    assert build_artifact is not None
