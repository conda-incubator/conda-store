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


def test_api_list_namespace_unauth(testclient):
    response = testclient.get('api/v1/namespace')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.Namespace], r.data)
    assert data == [schema.Namespace(id=1, name="default")]


def test_api_list_environments_unauth(testclient):
    response = testclient.get('api/v1/environment')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.Environment], r.data)
    assert data == []


def test_api_list_builds_unauth(testclient):
    response = testclient.get('api/v1/build')

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    data = parse_obj_as(List[schema.Build], r.data)
    assert data == []
