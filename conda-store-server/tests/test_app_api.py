from conda_store_server import api, schema


def test_conda_store_app_register_solve(conda_store, celery_worker):
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=["conda-forge"],
        dependencies=["conda-store-server"],
    )

    task, solve_id = conda_store.register_solve(conda_specification)
    solve = api.get_solve(conda_store.db, solve_id=solve_id)

    assert solve is not None
    assert solve.started_on is None
    assert solve.ended_on is None
    assert solve.package_builds == []
    assert solve.specification.spec["name"] == conda_specification.name
    assert solve.specification.spec["channels"] == conda_specification.channels
    assert solve.specification.spec["dependencies"] == conda_specification.dependencies

    # wait for task to complete
    task.get()
    assert task.state == "SUCCESS"

    conda_store.db.expire_all()
    assert solve.ended_on is not None
    assert len(solve.package_builds) > 0


def test_conda_store_register_environment(conda_store):
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=["conda-forge"],
        dependencies=["conda-store-server"],
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
    # when new environment is created current_build should be the build
    assert build.environment.current_build == build
