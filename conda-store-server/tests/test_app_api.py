from conda_store_server import api, schema


def test_conda_store_app_register_solve(conda_store, celery_worker):
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=["main"],
        dependencies=["python"],
    )

    task_id, solve_id = conda_store.register_solve(conda_specification)
    solve = api.get_solve(conda_store.db, solve_id=solve_id)

    assert solve is not None
    assert solve.started_on is None
    assert solve.ended_on is None
    assert solve.package_builds == []
    assert solve.specification.spec["name"] == conda_specification.name
    assert solve.specification.spec["channels"] == conda_specification.channels
    assert solve.specification.spec["dependencies"] == conda_specification.dependencies

    # wait for task to complete
    from celery.result import AsyncResult

    task = AsyncResult(task_id)
    task.get(timeout=30)
    assert task.state == "SUCCESS"

    conda_store.db.expire_all()
    assert solve.ended_on is not None
    assert len(solve.package_builds) > 0


def test_conda_store_register_environment(conda_store, celery_worker):
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=["main"],
        dependencies=["python"],
    )
    namespace_name = "pytest-namespace"

    build_id = conda_store.register_environment(
        specification=conda_specification.dict(), namespace=namespace_name
    )

    build = api.get_build(conda_store.db, build_id=build_id)
    assert build is not None
    assert build.status == schema.BuildStatus.QUEUED
    assert build.environment.name == conda_specification.name
    assert build.environment.namespace.name == namespace_name
    assert build.specification.spec["name"] == conda_specification.name
    assert build.specification.spec["channels"] == conda_specification.channels
    assert build.specification.spec["dependencies"] == conda_specification.dependencies
    # when new environment is created current_build should be the default build
    assert build.environment.current_build == build

    from celery.result import AsyncResult

    # wait for task to complete
    # build: environment, export, archive

    task = AsyncResult(f"build-{build.id}-environment")
    task.wait(timeout=60)

    task = AsyncResult(f"build-{build.id}-conda-env-export")
    task.wait(timeout=60)

    task = AsyncResult(f"build-{build.id}-conda-pack")
    task.wait(timeout=60)

    task = AsyncResult(f"build-{build.id}-docker")
    task.get(timeout=2*60, propagate=False)
    # currently docker images are failing to build
    task.state == "FAILED"

    conda_store.db.expire_all()
    assert build.status == schema.BuildStatus.COMPLETED
