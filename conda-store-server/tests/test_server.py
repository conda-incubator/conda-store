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

    environment_yaml = response.content.decode("utf-8")
    assert "name:" in environment_yaml
    assert "channels:" in environment_yaml
    assert "dependencies:" in environment_yaml


def test_api_get_build_two_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/1010101010101")
    response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_conda_channels_unauth(testclient):
    response = testclient.get("api/v1/channel")
    response.raise_for_status()

    r = schema.APIListCondaChannel.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    api_channels = set(_.name for _ in r.data)
    assert api_channels == {
        "https://conda.anaconda.org/conda-forge",
    }
