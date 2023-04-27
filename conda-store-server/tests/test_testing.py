from conda_store_server import schema, testing, api


def test_testing_initialize_database(conda_store):
    config = {
        "namespace1": {
            "name1": schema.CondaSpecification(
                name="name1",
                channels=["conda-forge"],
                dependencies=["numpy"],
            ),
            "name2": schema.CondaSpecification(
                name="name2",
                channels=["defaults"],
                dependencies=["flask"],
            ),
        },
        "namespace2": {
            "name3": schema.CondaSpecification(
                name="name3",
                channels=["bioconda"],
                dependencies=["numba"],
            )
        },
    }

    testing.initialize_database(conda_store.db, config)

    assert len(api.list_namespaces(conda_store.db).all()) == 2
    assert len(api.list_environments(conda_store.db).all()) == 3
    assert len(api.list_builds(conda_store.db).all()) == 3
    assert len(api.list_solves(conda_store.db).all()) == 3
