from conda_store_server import api, schema


def test_conda_store_app_register_solve(conda_store):
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=['conda-forge'],
        dependencies=['conda-store-server']
    )

    test, solve_id = conda_store.register_solve(conda_specification)

    solve = api.get_solve(conda_store.db, solve_id=solve_id)

    assert solve is not None
    assert solve.started_on == None
    assert solve.ended_on == None
    assert solve.package_builds == []
    assert solve.specification.spec['name'] == conda_specification.name
    assert solve.specification.spec['channels'] == conda_specification.channels
    assert solve.specification.spec['dependencies'] == conda_specification.dependencies


def test_conda_store_register_environment(conda_store):
    conda_specification = schema.CondaSpecification(
        name="pytest-name",
        channels=['conda-forge'],
        dependencies=['conda-store-server']
    )
    namespace_name = "pytest-namespace"

    build_id = conda_store.register_environment(
        specification=conda_specification.dict(),
        namespace=namespace_name
    )

    build = api.get_build(conda_store.db, build_id=build_id)
    assert build is not None
    assert build.environment.name == conda_specification.name
    assert build.environment.namespace.name == namespace_name
    assert build.specification.spec['name'] == conda_specification.name
    assert build.specification.spec['channels'] == conda_specification.channels
    assert build.specification.spec['dependencies'] == conda_specification.dependencies
    # when new environment is created current_build should be the build
    assert build.environment.current_build == build
