from conda_store_server import api


def test_namespace_crud(conda_store):
    namespace_name = "pytest-namespace"

    # starts with no namespaces for test
    assert len(api.list_namespaces(conda_store.db).all()) == 0

    # create namespace
    namespace = api.create_namespace(conda_store.db, name=namespace_name)
    conda_store.db.commit()

    # check that only one namespace exists
    assert len(api.list_namespaces(conda_store.db).all()) == 1

    # check that ensuring a namespace doesn't create a new one
    api.ensure_namespace(conda_store.db, name=namespace_name)

    assert len(api.list_namespaces(conda_store.db).all()) == 1

    # check that getting namespace works
    namespace = api.get_namespace(conda_store.db, id=namespace.id)
    assert namespace is not None

    # check that deleting a namespace works
    api.delete_namespace(conda_store.db, id=namespace.id)
    conda_store.db.commit()

    assert len(api.list_namespaces(conda_store.db).all()) == 0

    # check that ensuring a namespace doesn't creates one
    api.ensure_namespace(conda_store.db, name=namespace_name)

    assert len(api.list_namespaces(conda_store.db).all()) == 1


def test_environment_crud(conda_store):
    namespace_name = "pytest-namespace"
    environment_name = "pytest-environment"
    description = "Hello World"

    namespace = api.ensure_namespace(conda_store.db, name=namespace_name)

    assert len(api.list_environments(conda_store.db).all()) == 0

    # create environment
    environment = api.create_environment(
        conda_store.db,
        namespace_id=namespace.id,
        name=environment_name,
        description=description,
    )
    conda_store.db.commit()

    # check that only one environment exists
    assert len(api.list_environments(conda_store.db).all()) == 1

    # ensure environment
    api.ensure_environment(
        conda_store.db, name=environment_name, namespace_id=namespace.id
    )

    assert len(api.list_environments(conda_store.db).all()) == 1

    # check that getting environment works
    environment = api.get_environment(
        conda_store.db, namespace_id=namespace.id, name=environment_name
    )
    assert environment is not None

    # # check that deleting a environment works
    # api.delete_environment(conda_store.db, namespace_id=namespace.id, name=environment_name)
    # conda_store.db.commit()

    # assert len(api.list_environment(conda_store.db).all()) == 0

    # # check that ensuring a environment doesn't creates one
    # api.ensure_environment(conda_store.db, name=environment_name, namespace_id=namespace.id)

    # assert len(api.list_environments(conda_store.db).all()) == 1


def test_get_set_keyvaluestore(conda_store):
    setting_1 = {"a": 1, "b": 2}
    setting_2 = {"c": 1, "d": 2}
    setting_3 = {"e": 1, "f": 2}

    api.set_kvstore_key_values(conda_store.db, "setting", setting_1)
    api.set_kvstore_key_values(conda_store.db, "setting/1", setting_2)
    api.set_kvstore_key_values(conda_store.db, "setting/1/2", setting_3)

    assert setting_1 == api.get_kvstore_key_values(conda_store.db, "setting")
    assert setting_2 == api.get_kvstore_key_values(conda_store.db, "setting/1")
    assert setting_3 == api.get_kvstore_key_values(conda_store.db, "setting/1/2")

    # test updating a prefix
    api.set_kvstore_key_values(conda_store.db, "setting", setting_2)
    assert {**setting_1, **setting_2} == api.get_kvstore_key_values(
        conda_store.db, "setting"
    )
    breakpoint()

    # test updating a prefix
    api.set_kvstore_key_values(
        conda_store.db, "setting", {"c": 999, "d": 999}, update=False
    )
    assert {**setting_1, **setting_2} == api.get_kvstore_key_values(
        conda_store.db, "setting"
    )
