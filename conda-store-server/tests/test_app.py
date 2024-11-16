# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import sys

import pytest
from celery.result import AsyncResult

from conda_store_server import api
from conda_store_server._internal import action, conda_utils, schema


@pytest.mark.long_running_test
def test_conda_store_app_register_solve(
    db, conda_store, simple_specification, simple_conda_lock, celery_worker
):
    """Test that CondaStore can register Solve objects and dispatch solve tasks."""
    task_id, solve_id = conda_store.register_solve(db, simple_specification)
    action.action_add_lockfile_packages(
        db=db,
        conda_lock_spec=simple_conda_lock,
        solve_id=solve_id,
    )
    solve = api.get_solve(db, solve_id=solve_id)
    platform = conda_utils.conda_platform()

    assert solve is not None
    assert solve.started_on is None
    assert solve.ended_on is None
    assert len(solve.package_builds) == len(
        [item for item in simple_conda_lock["package"] if item["platform"] == platform]
    )
    assert solve.specification.spec["name"] == simple_specification.name
    assert solve.specification.spec["channels"] == simple_specification.channels
    assert solve.specification.spec["dependencies"] == simple_specification.dependencies
    task = AsyncResult(task_id)
    task.get(timeout=30)
    assert task.state == "SUCCESS"

    db.expire_all()
    assert solve.ended_on is not None
    assert len(solve.package_builds) > 0


@pytest.mark.long_running_test
def test_conda_store_register_environment_workflow(
    db, simple_specification, conda_store, celery_worker
):
    """Test entire environment build workflow."""
    namespace_name = "pytest-namespace"

    build_id = conda_store.register_environment(
        db, specification=simple_specification.model_dump(), namespace=namespace_name
    )

    build = api.get_build(db, build_id=build_id)
    assert build is not None
    assert build.status in [schema.BuildStatus.QUEUED, schema.BuildStatus.COMPLETED]
    assert build.environment.name == simple_specification.name
    assert build.environment.namespace.name == namespace_name
    assert build.specification.spec["name"] == simple_specification.name
    assert build.specification.spec["channels"] == simple_specification.channels
    assert build.specification.spec["dependencies"] == simple_specification.dependencies
    # when new environment is created current_build should be the default build
    assert build.environment.current_build == build

    # wait for task to complete
    # build: environment, export, archive
    # docker is expected to fail will be fixed soon

    task = AsyncResult(f"build-{build.id}-environment")
    task.wait(timeout=60)

    task = AsyncResult(f"build-{build.id}-conda-env-export")
    task.wait(timeout=60)

    task = AsyncResult(f"build-{build.id}-conda-pack")
    task.wait(timeout=60)

    if sys.platform == "linux":
        task = AsyncResult(f"build-{build.id}-docker")
        task.wait(timeout=2 * 60)

    task = AsyncResult(f"build-{build.id}-constructor-installer")
    task.wait(timeout=5 * 60)

    db.expire_all()
    assert build.status == schema.BuildStatus.COMPLETED


def test_conda_store_register_environment_force_false_same_namespace(db, conda_store):
    """Ensure behavior that when force=False and same namespace the
    same spec does not trigger another build

    """
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=["main"],
        dependencies=["python"],
    )
    namespace_name = "pytest-namespace"

    first_build_id = conda_store.register_environment(
        db,
        specification=conda_specification.model_dump(),
        namespace=namespace_name,
        force=False,
    )

    second_build_id = conda_store.register_environment(
        db,
        specification=conda_specification.model_dump(),
        namespace=namespace_name,
        force=False,
    )

    assert first_build_id == 1
    assert second_build_id is None


def test_conda_store_register_environment_force_false_different_namespace(
    db, conda_store
):
    """Ensure behavior that when force=False and different namespace
    the same spec still triggers another build

    """
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=["main"],
        dependencies=["python"],
    )

    first_build_id = conda_store.register_environment(
        db,
        specification=conda_specification.model_dump(),
        namespace="pytest-namespace",
        force=False,
    )

    second_build_id = conda_store.register_environment(
        db,
        specification=conda_specification.model_dump(),
        namespace="pytest-different-namespace",
        force=False,
    )

    assert first_build_id == 1
    assert second_build_id == 2


def test_conda_store_register_environment_duplicate_force_true(db, conda_store):
    """Ensure behavior that when force=True the same spec in same
    namespace still triggers another build

    """
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=["main"],
        dependencies=["python"],
    )
    namespace_name = "pytest-namespace"

    first_build_id = conda_store.register_environment(
        db,
        specification=conda_specification.model_dump(),
        namespace=namespace_name,
        force=True,
    )

    second_build_id = conda_store.register_environment(
        db,
        specification=conda_specification.model_dump(),
        namespace=namespace_name,
        force=True,
    )

    assert first_build_id == 1
    assert second_build_id == 2
