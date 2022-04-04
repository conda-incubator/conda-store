"""These tests an assumption
`tests/assets/environments/python-flask-env.yaml` is the first
environment added to conda-store.  The given environment has build 1
and has completed building.

List methods cannot be fully tested "exactly" since additional
environments/builds may have been created which would change the
ordering for tests.

"""
import json
import uuid
from typing import List

from pydantic import parse_obj_as

import conda_store_server
from conda_store_server import schema


def test_api_status_unauth(testclient):
    response = testclient.get('api/v1/')
    response.raise_for_status()

    r = schema.APIGetStatus.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.version == conda_store_server.__version__


def test_api_permissions_unauth(testclient):
    response = testclient.get('api/v1/permission/')
    response.raise_for_status()

    r = schema.APIGetPermission.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.authenticated == False
    assert r.data.primary_namespace == "default"
    assert r.data.entity_permissions == {
            "default/*": [
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.NAMESPACE_READ.value,
            ]
    }


def test_api_permissions_auth(testclient):
    testclient.login()
    response = testclient.get('api/v1/permission/')
    response.raise_for_status()

    r = schema.APIGetPermission.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.authenticated == True
    assert r.data.primary_namespace == "username"
    assert r.data.entity_permissions == {
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


def test_api_list_namespace_unauth(testclient):
    response = testclient.get('api/v1/namespace')
    response.raise_for_status()

    r = schema.APIListNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    # by default unauth only has access to the default namespace
    assert len(r.data) == 1


def test_api_list_namespace_auth(testclient):
    testclient.login()
    response = testclient.get('api/v1/namespace')
    response.raise_for_status()

    r = schema.APIListNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    # by default auth has at least two environments created
    # `default` and `filesystem`
    assert len(r.data) >= 2


def test_api_get_namespace_unauth(testclient):
    response = testclient.get('api/v1/namespace/default')
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == "default"


def test_api_get_namespace_unauth_no_exist(testclient):
    response = testclient.get('api/v1/namespace/wrong')
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_namespace_auth(testclient):
    testclient.login()
    response = testclient.get('api/v1/namespace/filesystem')
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == "filesystem"


def test_api_get_namespace_auth_no_exist(testclient):
    testclient.login()
    response = testclient.get('api/v1/namespace/wrong')

    assert response.status_code == 404
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_environments_unauth(testclient):
    response = testclient.get('api/v1/environment')
    response.raise_for_status()

    r = schema.APIListEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_api_list_environments_auth(testclient):
    testclient.login()
    response = testclient.get('api/v1/environment')
    response.raise_for_status()

    r = schema.APIListEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) >= 1


def test_api_get_environment_unauth(testclient):
    response = testclient.get('api/v1/environment/filesystem/python-flask-env')
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_environment_auth_existing(testclient):
    testclient.login()
    response = testclient.get('api/v1/environment/filesystem/python-flask-env')
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.namespace.name == "filesystem"
    assert r.data.name == "python-flask-env"


def test_api_get_environment_auth_not_existing(testclient):
    testclient.login()
    response = testclient.get('api/v1/environment/filesystem/wrong')
    assert response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_builds_unauth(testclient):
    response = testclient.get('api/v1/build')
    response.raise_for_status()

    r = schema.APIListBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_api_list_builds_auth(testclient):
    testclient.login()
    response = testclient.get('api/v1/build')
    response.raise_for_status()

    r = schema.APIListBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) >= 1


def test_api_get_build_one_unauth(testclient):
    response = testclient.get('api/v1/build/1')
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth(testclient):
    testclient.login()
    response = testclient.get('api/v1/build/1')
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.id == 1
    assert r.data.specification.name == "python-flask-env"
    assert r.data.status == schema.BuildStatus.COMPLETED.value


def test_api_get_build_one_unauth_packages(testclient):
    response = testclient.get('api/v1/build/1/packages')
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth_packages(testclient):
    testclient.login()
    response = testclient.get('api/v1/build/1/packages?size=5')
    response.raise_for_status()

    r = schema.APIListCondaPackage.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 5


def test_api_get_build_auth_packages_no_exist(testclient):
    testclient.login()
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
    testclient.login()
    response = testclient.get('api/v1/build/1/logs')
    response.raise_for_status()

    logs = response.content.decode('utf-8')
    assert "Preparing transaction:" in logs
    assert "Executing transaction:" in logs


def test_api_get_build_auth_logs_no_exist(testclient):
    testclient.login()
    response = testclient.get('api/v1/build/10101010101/logs')
    assert response.status_code == 404


def test_api_get_build_one_unauth_yaml(testclient):
    response = testclient.get('api/v1/build/1/yaml/')
    assert response.status_code == 403


def test_api_get_build_one_auth_yaml(testclient):
    testclient.login()
    response = testclient.get('api/v1/build/1/yaml/')
    response.raise_for_status()

    environment_yaml = response.content.decode('utf-8')
    assert "name:" in environment_yaml
    assert "channels:" in environment_yaml
    assert "dependencies:" in environment_yaml


def test_api_get_build_two_auth(testclient):
    testclient.login()
    response = testclient.get('api/v1/build/1010101010101')
    response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_conda_channels_unauth(testclient):
    response = testclient.get('api/v1/channel')
    response.raise_for_status()

    r = schema.APIListCondaChannel.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    api_channels = set(_.name for _ in r.data)
    assert api_channels == {
        'https://conda.anaconda.org/main',
        'https://conda.anaconda.org/conda-forge'
    }


def test_api_list_conda_packages_unauth(testclient):
    response = testclient.get('api/v1/package?size=15')
    response.raise_for_status()

    r = schema.APIListCondaPackage.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 15


# ============ MODIFICATION =============

def test_create_specification_uauth(testclient):
    namespace = 'default'
    environment_name = f'pytest-{uuid.uuid4()}'

    response = testclient.post('api/v1/specification', json={
        'namespace': namespace,
        'specification': json.dumps({
            'name': environment_name
        })
    })
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_create_specification_auth(testclient):
    namespace = 'default'
    environment_name = f'pytest-{uuid.uuid4()}'

    testclient.login()
    response = testclient.post('api/v1/specification', json={
        'namespace': namespace,
        'specification': json.dumps({
            'name': environment_name
        })
    })
    response.raise_for_status()

    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    # check for the given build
    response = testclient.get(f'api/v1/build/{r.data.build_id}')
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.specification.name == environment_name

    # check for the given environment
    response = testclient.get(f'api/v1/environment/{namespace}/{environment_name}')
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.data.namespace.name == namespace


def test_create_specification_auth_no_namespace_specified(testclient):
    namespace = 'username' # same as login username
    environment_name = f'pytest-{uuid.uuid4()}'

    testclient.login()
    response = testclient.post('api/v1/specification', json={
        'specification': json.dumps({
            'name': environment_name
        })
    })
    response.raise_for_status()

    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    # check for the given build
    response = testclient.get(f'api/v1/build/{r.data.build_id}')
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.specification.name == environment_name

    # check for the given environment
    response = testclient.get(f'api/v1/environment/{namespace}/{environment_name}')
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.data.namespace.name == namespace


def test_put_build_trigger_build_noauth(testclient):
    build_id = 1

    response = testclient.put(f'api/v1/build/{build_id}')
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_put_build_trigger_build_auth(testclient):
    build_id = 1

    testclient.login()
    response = testclient.put(f'api/v1/build/{build_id}')
    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f'api/v1/build/{r.data.build_id}')
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_create_namespace_noauth(testclient):
    namespace = f"pytest-{uuid.uuid4()}"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_create_namespace_auth(testclient):
    namespace = f"pytest-{uuid.uuid4()}"

    testclient.login()
    response = testclient.post(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == namespace


def test_create_get_delete_namespace_auth(testclient):
    namespace = f"pytest-delete-ns-{uuid.uuid4()}"

    testclient.login()
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


# def test_update_environment_build(testclient):
#     # PUT /api/v1/environment/namespace/name
#     pass


# def test_delete_environment(testclient):
#     # DELETE /api/v1/environment/namespace/name
#     pass


def test_delete_build_auth(testclient):
    build_id = 1

    testclient.login()
    response = testclient.put(f'api/v1/build/{build_id}')
    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    new_build_id = r.data.build_id

    response = testclient.get(f'api/v1/build/{new_build_id}')
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    # currently you cannot delete a build before it succeeds or fails
    response = testclient.delete(f'api/v1/build/{new_build_id}')
    assert response.status_code == 400

    # r = schema.APIAckResponse.parse_obj(response.json())
    # assert r.status == schema.APIStatus.OK

    # response = testclient.get(f'api/v1/build/{new_build_id}')
    # assert response.status_code == 404

    # r = schema.APIResponse.parse_obj(response.json())
    # assert r.status == schema.APIStatus.ERROR
