import pytest
from conda_store_server import api
from conda_store_server.orm import NamespaceRoleMapping


def test_namespace_crud(db):
    namespace_name = "pytest-namespace"

    # starts with no namespaces for test
    assert len(api.list_namespaces(db).all()) == 0

    # create namespace
    namespace = api.create_namespace(db, name=namespace_name)
    db.commit()

    # check that only one namespace exists
    assert len(api.list_namespaces(db).all()) == 1

    # check that ensuring a namespace doesn't create a new one
    api.ensure_namespace(db, name=namespace_name)

    assert len(api.list_namespaces(db).all()) == 1

    # check that getting namespace works
    namespace = api.get_namespace(db, id=namespace.id)
    assert namespace is not None

    # check that deleting a namespace works
    api.delete_namespace(db, id=namespace.id)
    db.commit()

    assert len(api.list_namespaces(db).all()) == 0

    # check that ensuring a namespace doesn't creates one
    api.ensure_namespace(db, name=namespace_name)

    assert len(api.list_namespaces(db).all()) == 1


def test_namespace_role_mapping(db):
    namespace_name = "pytest-namespace"

    # starts with no namespaces for test
    assert len(api.list_namespaces(db).all()) == 0

    # create namespace
    namespace = api.create_namespace(db, name=namespace_name)
    db.commit()

    # check that only one namespace exists
    assert len(api.list_namespaces(db).all()) == 1

    # create a Role Mapping, with a failing entity
    with pytest.raises(Exception):
        NamespaceRoleMapping(
            namespace=namespace, namespace_id=namespace.id, entity="invalid_entity_name"
        )

    # Creates role mappings with valid entity names
    NamespaceRoleMapping(namespace=namespace, namespace_id=namespace.id, entity="org/*")

    NamespaceRoleMapping(
        namespace=namespace, namespace_id=namespace.id, entity="*/team"
    )

    NamespaceRoleMapping(
        namespace=namespace, namespace_id=namespace.id, entity="org/team"
    )

    NamespaceRoleMapping(namespace=namespace, namespace_id=namespace.id, entity="*/*")


def test_environment_crud(db):
    namespace_name = "pytest-namespace"
    environment_name = "pytest-environment"
    description = "Hello World"

    namespace = api.ensure_namespace(db, name=namespace_name)

    assert len(api.list_environments(db).all()) == 0

    # create environment
    environment = api.create_environment(
        db,
        namespace_id=namespace.id,
        name=environment_name,
        description=description,
    )
    db.commit()

    # check that only one environment exists
    assert len(api.list_environments(db).all()) == 1

    # ensure environment
    api.ensure_environment(db, name=environment_name, namespace_id=namespace.id)

    assert len(api.list_environments(db).all()) == 1

    # check that getting environment works
    environment = api.get_environment(
        db, namespace_id=namespace.id, name=environment_name
    )
    assert environment is not None

    # # check that deleting a environment works
    # api.delete_environment(conda_store.db, namespace_id=namespace.id, name=environment_name)
    # conda_store.db.commit()

    # assert len(api.list_environment(conda_store.db).all()) == 0

    # # check that ensuring a environment doesn't creates one
    # api.ensure_environment(conda_store.db, name=environment_name, namespace_id=namespace.id)

    # assert len(api.list_environments(conda_store.db).all()) == 1


def test_get_set_keyvaluestore(db):
    setting_1 = {"a": 1, "b": 2}
    setting_2 = {"c": 1, "d": 2}
    setting_3 = {"e": 1, "f": 2}

    api.set_kvstore_key_values(db, "pytest", setting_1)
    api.set_kvstore_key_values(db, "pytest/1", setting_2)
    api.set_kvstore_key_values(db, "pytest/1/2", setting_3)

    assert setting_1 == api.get_kvstore_key_values(db, "pytest")
    assert setting_2 == api.get_kvstore_key_values(db, "pytest/1")
    assert setting_3 == api.get_kvstore_key_values(db, "pytest/1/2")

    # test updating a prefix
    api.set_kvstore_key_values(db, "pytest", setting_2)
    assert {**setting_1, **setting_2} == api.get_kvstore_key_values(db, "pytest")

    # test updating a prefix
    api.set_kvstore_key_values(db, "pytest", {"c": 999, "d": 999}, update=False)
    assert {**setting_1, **setting_2} == api.get_kvstore_key_values(db, "pytest")
