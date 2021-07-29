import pytest

from conda_store_server.auth import RBACAuthorization, Permissions

@pytest.mark.parametrize('entity_bindings,arn,permissions,authorized', [
    (
        {
            'example-namespace/example-name': {'developer'},
        },
        'example-namespace/example-name',
        {
            Permissions.ENVIRONMENT_CREATE
        },
        True
     ),
    (
        {
            'example-namespace/example-name': {'developer', 'viewer'},
        },
        'example-namespace/example-name',
        {
            Permissions.ENVIRONMENT_DELETE
        },
        True
     ),
    (
        {
            'e*/e*am*': {'admin'},
        },
        'example-namespace/example-name',
        {
            Permissions.ENVIRONMENT_CREATE
        },
        True
     ),
    (
        {
            'e*/e*am*': {'viewer'},
        },
        'example-namespace/example-name',
        {
            Permissions.ENVIRONMENT_CREATE
        },
        False
     ),
])
def test_environent_auth(entity_bindings, arn, permissions, authorized):
    authorization = RBACAuthorization()
    assert authorized == authorization.authorized(entity_bindings, arn, permissions)
