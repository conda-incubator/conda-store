from typing import List

from pydantic import parse_obj_as

import conda_store_server
from conda_store_server import schema


def test_api_status_unauth(testclient):
    response = testclient.get('api/v1/')
    r = schema.APIResponse.parse_obj(response.json())

    assert r.status == schema.APIStatus.OK
    assert r.data == {"version": conda_store_server.__version__}


def test_api_permissions_unauth(testclient):
    response = testclient.get('api/v1/permission/')
    r = schema.APIResponse.parse_obj(response.json())

    assert r.status == schema.APIStatus.OK
    assert r.data == {
        "authenticated": False,
        "primary_namespace": "default",
        "entity_permissions": {
            "default/*": [
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.NAMESPACE_READ.value,
            ]
        }
    }


def test_api_permissions_auth(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/permission/')
    r = schema.APIResponse.parse_obj(response.json())

    assert r.status == schema.APIStatus.OK
    assert r.data == {
        "authenticated": True,
        "primary_namespace": "username",
        "entity_permissions": {
            "*/*": sorted([
                schema.Permissions.ENVIRONMENT_CREATE.value,
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.ENVIRONMENT_UPDATE.value,
                schema.Permissions.ENVIRONMENT_DELETE.value,
                schema.Permissions.BUILD_DELETE.value,
                schema.Permissions.NAMESPACE_CREATE.value,
                schema.Permissions.NAMESPACE_READ.value,
                schema.Permissions.NAMESPACE_DELETE.value,
            ]),
            "default/*": sorted([
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.NAMESPACE_READ.value,
            ]),
            "filesystem/*": sorted([
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.NAMESPACE_READ.value,
            ])
        }
    }


def test_api_list_namespace_unauth(testclient):
    response = testclient.get('api/v1/namespace')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.Namespace], r.data)
    assert data == [schema.Namespace(id=1, name="default")]


def test_api_get_namespace_unauth(testclient):
    response = testclient.get('api/v1/namespace/default')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(schema.Namespace, r.data)
    assert data.id == 1
    assert data.name == "default"


def test_api_get_namespace_unauth_no_exist(testclient):
    response = testclient.get('api/v1/namespace/wrong')

    assert response.status_code == 403
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_namespace_auth(testclient):
    response = testclient.get('api/v1/namespace/default')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(schema.Namespace, r.data)
    assert data.id == 1
    assert data.name == "default"


def test_api_get_namespace_auth_no_exist(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/namespace/wrong')

    assert response.status_code == 404
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_environments_unauth(testclient):
    response = testclient.get('api/v1/environment')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.Environment], r.data)
    assert data == []


def test_api_list_environments_auth(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/environment')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.Environment], r.data)
    assert len(data) == 1
    assert data[0].namespace.name == "filesystem"
    assert data[0].name == "python-flask-env"


def test_api_get_environment_unauth(testclient):
    response = testclient.get('api/v1/environment/filesystem/python-flask-env')

    assert response.status_code == 403
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_environment_auth_existing(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/environment/filesystem/python-flask-env')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(schema.Environment, r.data)
    assert data.namespace.name == "filesystem"
    assert data.name == "python-flask-env"


def test_api_get_environment_auth_not_existing(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/environment/filesystem/wrong')

    print(response.content)
    assert response.status_code == 404
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_builds_unauth(testclient):
    response = testclient.get('api/v1/build')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.Build], r.data)
    assert data == []


def test_api_list_builds_auth(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/build')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.Build], r.data)

    assert len(data) == 1
    assert data[0].id == 1
    assert data[0].status == schema.BuildStatus.COMPLETED.value


def test_api_get_build_one_unauth(testclient):
    response = testclient.get('api/v1/build/1')

    assert response.status_code == 403
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_unauth_packages(testclient):
    response = testclient.get('api/v1/build/1/packages')

    assert response.status_code == 403
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth_packages(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/build/1/packages?size=5')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.CondaPackage], r.data)
    assert len(data) == 5


def test_api_get_build_auth_packages_no_exist(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/build/101010101/packages')

    assert response.status_code == 404
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_unauth_logs(testclient):
    response = testclient.get('api/v1/build/1/logs')

    assert response.status_code == 403
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth_logs(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/build/1/logs')
    logs = response.content.decode('utf-8')
    assert "Preparing transaction:" in logs
    assert "Executing transaction:" in logs


def test_api_get_build_auth_logs_no_exist(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/build/10101010101/logs')
    assert response.status_code == 404


def test_api_get_build_one_auth(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/build/1')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(schema.Build, r.data)
    assert data.id == 1
    assert data.specification.name == "python-flask-env"
    assert data.status == schema.BuildStatus.COMPLETED.value


def test_api_get_build_one_unauth_yaml(testclient):
    response = testclient.get('api/v1/build/1/yaml/')
    assert response.status_code == 403


def test_api_get_build_one_auth_yaml(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/build/1/yaml/')
    environment_yaml = response.content.decode('utf-8')
    assert "name:" in environment_yaml
    assert "channels:" in environment_yaml
    assert "dependencies:" in environment_yaml


def test_api_get_build_two_auth(testclient):
    testclient.login(username="username", password="password")
    response = testclient.get('api/v1/build/1010101010101')

    response.status_code == 404
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_conda_channels_unauth(testclient):
    response = testclient.get('api/v1/channel')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.CondaChannel], r.data)
    api_channels = set(_.name for _ in data)
    assert api_channels == {
        'https://conda.anaconda.org/main',
        'https://conda.anaconda.org/conda-forge'
    }


def test_api_list_conda_packages_unauth(testclient):
    response = testclient.get('api/v1/package?size=15')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.CondaPackage], r.data)
    assert len(data) == 15
