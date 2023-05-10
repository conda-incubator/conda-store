import yaml
import json

from conda_store_server import __version__, schema


def test_api_version_unauth(testclient):
    response = testclient.get("/api/v1/")
    response.raise_for_status()

    r = schema.APIGetStatus.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.version == __version__


def test_api_permissions_unauth(testclient):
    response = testclient.get("api/v1/permission/")
    response.raise_for_status()

    r = schema.APIGetPermission.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.authenticated is False
    assert r.data.primary_namespace == "default"
    assert r.data.entity_permissions == {
        "default/*": [
            schema.Permissions.ENVIRONMENT_READ.value,
            schema.Permissions.NAMESPACE_READ.value,
        ]
    }


def test_api_permissions_auth(testclient, authenticate):
    response = testclient.get("api/v1/permission/")
    response.raise_for_status()

    r = schema.APIGetPermission.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.authenticated is True
    assert r.data.primary_namespace == "username"
    assert r.data.entity_permissions == {
        "*/*": sorted(
            [
                schema.Permissions.ENVIRONMENT_CREATE.value,
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.ENVIRONMENT_UPDATE.value,
                schema.Permissions.ENVIRONMENT_DELETE.value,
                schema.Permissions.ENVIRONMENT_SOLVE.value,
                schema.Permissions.BUILD_DELETE.value,
                schema.Permissions.NAMESPACE_CREATE.value,
                schema.Permissions.NAMESPACE_READ.value,
                schema.Permissions.NAMESPACE_DELETE.value,
            ]
        ),
        "default/*": sorted(
            [
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.NAMESPACE_READ.value,
            ]
        ),
        "filesystem/*": sorted(
            [
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.NAMESPACE_READ.value,
            ]
        ),
    }


def test_api_list_namespace_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/namespace")
    response.raise_for_status()

    r = schema.APIListNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    # by default unauth only has access to the default namespace
    assert len(r.data) == 1
    assert r.data[0].name == "default"


def test_api_list_namespace_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/namespace")
    response.raise_for_status()

    r = schema.APIListNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert sorted([_.name for _ in r.data]) == ["default", "namespace1", "namespace2"]


def test_api_get_namespace_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/namespace/default")
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == "default"


def test_api_get_namespace_unauth_no_exist(testclient, seed_conda_store):
    response = testclient.get("api/v1/namespace/namespace1")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_namespace_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/namespace/namespace1")
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == "namespace1"


def test_api_get_namespace_auth_no_exist(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/namespace/wrong")

    assert response.status_code == 404
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_environments_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/environment")
    response.raise_for_status()

    r = schema.APIListEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert sorted([_.name for _ in r.data]) == ["name1", "name2"]


def test_api_list_environments_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/environment")
    response.raise_for_status()

    r = schema.APIListEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert sorted([_.name for _ in r.data]) == ["name1", "name2", "name3", "name4"]


def test_api_get_environment_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/environment/namespace1/name3")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_environment_auth_existing(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/environment/namespace1/name3")
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.namespace.name == "namespace1"
    assert r.data.name == "name3"


def test_api_get_environment_auth_not_existing(
    testclient, seed_conda_store, authenticate
):
    response = testclient.get("api/v1/environment/namespace1/wrong")
    assert response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_builds_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/build")
    response.raise_for_status()

    r = schema.APIListBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 2


def test_api_list_builds_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build")
    response.raise_for_status()

    r = schema.APIListBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 4


def test_api_get_build_one_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/build/3")  # namespace1/name3
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/3")
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.id == 3
    assert r.data.specification.name == "name3"
    assert r.data.status == schema.BuildStatus.QUEUED.value


def test_api_get_build_one_unauth_packages(testclient, seed_conda_store):
    response = testclient.get("api/v1/build/3/packages")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth_packages(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/3/packages")
    response.raise_for_status()

    r = schema.APIListCondaPackage.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 1


def test_api_get_build_auth_packages_no_exist(
    testclient, seed_conda_store, authenticate
):
    response = testclient.get("api/v1/build/101010101/packages")
    assert response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_unauth_logs(testclient, seed_conda_store):
    response = testclient.get("api/v1/build/3/logs")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth_logs(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/3/logs")
    response.raise_for_status()

    logs = response.content.decode("utf-8")
    assert "fake logs" in logs


def test_api_get_build_auth_logs_no_exist(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/10101010101/logs")
    assert response.status_code == 404


def test_api_get_build_one_unauth_yaml(testclient, seed_conda_store):
    response = testclient.get("api/v1/build/3/yaml/")
    assert response.status_code == 403


def test_api_get_build_one_auth_yaml(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/3/yaml/")
    response.raise_for_status()

    environment_yaml = yaml.safe_load(response.content.decode("utf-8"))
    assert {"name", "channels", "dependencies"} <= environment_yaml.keys()


def test_api_get_build_two_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/1010101010101")
    response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_conda_channels_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/channel")
    response.raise_for_status()

    r = schema.APIListCondaChannel.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    api_channels = set(_.name for _ in r.data)
    assert api_channels == {
        "https://conda.anaconda.org/conda-forge",
    }


def test_api_list_conda_packages_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/package")
    response.raise_for_status()

    r = schema.APIListCondaPackage.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 4


# ============ MODIFICATION =============


def test_create_specification_unauth(testclient):
    namespace = "default"
    environment_name = "pytest"

    response = testclient.post(
        "api/v1/specification",
        json={
            "namespace": namespace,
            "specification": json.dumps({"name": environment_name}),
        },
    )
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_create_specification_auth(testclient, celery_worker, authenticate):
    namespace = "default"
    environment_name = "pytest"

    response = testclient.post(
        "api/v1/specification",
        json={
            "namespace": namespace,
            "specification": json.dumps({"name": environment_name}),
        },
    )
    response.raise_for_status()

    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    # check for the given build
    response = testclient.get(f"api/v1/build/{r.data.build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.specification.name == environment_name

    # check for the given environment
    response = testclient.get(f"api/v1/environment/{namespace}/{environment_name}")
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.data.namespace.name == namespace


def test_create_specification_auth_no_namespace_specified(
    testclient, celery_worker, authenticate
):
    namespace = "username"  # same namespace as login
    environment_name = "pytest"

    response = testclient.post(
        "api/v1/specification",
        json={"specification": json.dumps({"name": environment_name})},
    )
    response.raise_for_status()

    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    # check for the given build
    response = testclient.get(f"api/v1/build/{r.data.build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.specification.name == environment_name

    # check for the given environment
    response = testclient.get(f"api/v1/environment/{namespace}/{environment_name}")
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.data.namespace.name == namespace


def test_put_build_trigger_build_noauth(testclient, seed_conda_store):
    build_id = 3

    response = testclient.put(f"api/v1/build/{build_id}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_put_build_trigger_build_auth(
    testclient, seed_conda_store, authenticate, celery_worker
):
    build_id = 1

    response = testclient.put(f"api/v1/build/{build_id}")
    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/build/{r.data.build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_create_namespace_noauth(testclient):
    namespace = "pytest"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_create_namespace_auth(testclient, authenticate):
    namespace = "pytest"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == namespace


def test_create_get_delete_namespace_auth(testclient, celery_worker, authenticate):
    namespace = "pytest-delete-namespace"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == namespace

    response = testclient.delete(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/namespace/{namespace}")
    assert response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_update_environment_build_unauth(testclient, seed_conda_store):
    namespace = "default"
    name = "name1"
    build_id = 1

    response = testclient.put(
        f"api/v1/environment/{namespace}/{name}", json={"build_id": build_id}
    )
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_update_environment_build_auth(
    testclient, seed_conda_store, authenticate, celery_worker
):
    namespace = "namespace2"
    name = "name4"
    build_id = 4

    response = testclient.put(
        f"api/v1/environment/{namespace}/{name}", json={"build_id": build_id}
    )
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/environment/{namespace}/{name}")
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.current_build_id == 4


def test_delete_environment_unauth(testclient, seed_conda_store):
    namespace = "namespace1"
    name = "name3"

    response = testclient.delete(f"api/v1/environment/{namespace}/{name}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_delete_environment_auth(
    testclient, seed_conda_store, authenticate, celery_worker
):
    namespace = "namespace1"
    environment_name = "name3"

    response = testclient.post(
        "api/v1/specification",
        json={
            "namespace": namespace,
            "specification": json.dumps({"name": environment_name}),
        },
    )
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.delete(f"api/v1/environment/{namespace}/{environment_name}")
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_delete_build_unauth(testclient, seed_conda_store):
    build_id = 4

    response = testclient.delete(f"api/v1/build/{build_id}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_delete_build_auth(testclient, seed_conda_store, authenticate, celery_worker):
    build_id = 4

    response = testclient.put(f"api/v1/build/{build_id}")
    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    new_build_id = r.data.build_id

    response = testclient.get(f"api/v1/build/{new_build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    # currently you cannot delete a build before it succeeds or fails
    # realistically you should be able to delete a build
    response = testclient.delete(f"api/v1/build/{new_build_id}")
    assert response.status_code == 400

    # r = schema.APIAckResponse.parse_obj(response.json())
    # assert r.status == schema.APIStatus.OK

    # response = testclient.get(f'api/v1/build/{new_build_id}')
    # assert response.status_code == 404

    # r = schema.APIResponse.parse_obj(response.json())
    # assert r.status == schema.APIStatus.ERROR
