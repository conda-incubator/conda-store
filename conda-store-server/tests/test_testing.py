from conda_store_server import api, schema, testing


def test_testing_initialize_database(db, conda_store):
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

    testing.seed_conda_store(db, conda_store, config)

    assert len(api.list_namespaces(db).all()) == 2
    assert len(api.list_environments(db).all()) == 3
    assert len(api.list_builds(db).all()) == 3
    assert len(api.list_solves(db).all()) == 3
    assert len(api.list_conda_packages(db).all()) == 3
