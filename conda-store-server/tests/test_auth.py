import datetime
import uuid

import pytest
from conda_store_server.schema import AuthenticationToken, Permissions
from conda_store_server.server.auth import (
    AuthenticationBackend,
    RBACAuthorizationBackend,
)


@pytest.mark.parametrize(
    "expression, resource, match",
    [
        ("e*/d*", "example/data", True),
        ("e*/d*", "example/eta", False),
        ("*e*d*/*e", "deed/rate", True),
    ],
)
def test_compile_arn_regex(expression, resource, match):
    regex = RBACAuthorizationBackend.compile_arn_regex(expression)
    assert (regex.match(resource) is not None) == match


@pytest.mark.parametrize(
    "expression, namespace, name",
    [
        ("e*/d*", "e%", "d%"),
        ("*e*d*/*e", "%e%d%", "%e"),
    ],
)
def test_compile_arn_sql_like(expression, namespace, name):
    result = RBACAuthorizationBackend.compile_arn_sql_like(expression)
    assert (namespace, name) == result


@pytest.mark.parametrize(
    "token_string,authenticated",
    [
        ("", False),
        ("asdf", False),
    ],
)
def test_authenticated(token_string, authenticated):
    authentication = AuthenticationBackend()
    authentication.secret = "supersecret"
    assert (authentication.authenticate(token_string) is not None) == authenticated


def test_valid_token():
    authentication = AuthenticationBackend()
    authentication.secret = "supersecret"

    token = authentication.encrypt_token(
        AuthenticationToken(
            primary_namespace="default",
            role_bindings={
                "default/*": ["viewer"],
                "e*/e*": ["admin"],
            },
        )
    )

    token_model = authentication.authenticate(token)
    assert isinstance(token_model, AuthenticationToken)


def test_expired_token():
    authentication = AuthenticationBackend()
    authentication.secret = "supersecret"

    token = authentication.encrypt_token(
        AuthenticationToken(
            primary_namespace="default",
            exp=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            role_bindings={
                "default/*": ["viewer"],
                "e*/e*": ["admin"],
            },
        )
    )

    assert authentication.authenticate(token) is None


@pytest.mark.parametrize(
    "entity_bindings,arn,permissions,authorized",
    [
        (
            {
                "example-namespace/example-name": {"developer"},
            },
            "example-namespace/example-name",
            {Permissions.ENVIRONMENT_CREATE},
            True,
        ),
        (
            {
                "example-namespace/example-name": {"developer", "viewer"},
            },
            "example-namespace/example-name",
            {Permissions.ENVIRONMENT_DELETE},
            False,
        ),
        (
            {
                "example-namespace/example-name": {"developer", "admin"},
            },
            "example-namespace/example-name",
            {Permissions.ENVIRONMENT_DELETE},
            True,
        ),
        (
            {
                "e*/e*am*": {"admin"},
            },
            "example-namespace/example-name",
            {Permissions.ENVIRONMENT_CREATE},
            True,
        ),
        (
            {
                "e*/e*am*": {"viewer"},
            },
            "example-namespace/example-name",
            {Permissions.ENVIRONMENT_CREATE},
            False,
        ),
    ],
)
def test_authorization(conda_store, entity_bindings, arn, permissions, authorized):
    authorization = RBACAuthorizationBackend(
        authentication_db=conda_store.session_factory
    )

    entity = AuthenticationToken(
        primary_namespace="example_namespace", role_bindings=entity_bindings
    )

    assert authorized == authorization.authorize(entity, arn, permissions)


_viewer_permissions = {
    Permissions.ENVIRONMENT_READ,
    Permissions.NAMESPACE_READ,
    Permissions.NAMESPACE_ROLE_MAPPING_READ,
}
_editor_permissions = {
    Permissions.BUILD_CANCEL,
    Permissions.ENVIRONMENT_CREATE,
    Permissions.ENVIRONMENT_READ,
    Permissions.ENVIRONMENT_UPDATE,
    Permissions.ENVIRONMENT_SOLVE,
    Permissions.NAMESPACE_READ,
    Permissions.NAMESPACE_ROLE_MAPPING_READ,
    Permissions.SETTING_READ,
}
_admin_permissions = {
    Permissions.BUILD_DELETE,
    Permissions.BUILD_CANCEL,
    Permissions.ENVIRONMENT_CREATE,
    Permissions.ENVIRONMENT_DELETE,
    Permissions.ENVIRONMENT_READ,
    Permissions.ENVIRONMENT_UPDATE,
    Permissions.ENVIRONMENT_SOLVE,
    Permissions.NAMESPACE_CREATE,
    Permissions.NAMESPACE_DELETE,
    Permissions.NAMESPACE_READ,
    Permissions.NAMESPACE_UPDATE,
    Permissions.NAMESPACE_ROLE_MAPPING_CREATE,
    Permissions.NAMESPACE_ROLE_MAPPING_READ,
    Permissions.NAMESPACE_ROLE_MAPPING_UPDATE,
    Permissions.NAMESPACE_ROLE_MAPPING_DELETE,
    Permissions.SETTING_READ,
    Permissions.SETTING_UPDATE,
}


@pytest.mark.parametrize(
    "role, permissions",
    [
        ("viewer", _viewer_permissions),
        ("developer", _editor_permissions),
        ("editor", _editor_permissions),
        ("admin", _admin_permissions),
    ],
)
@pytest.mark.parametrize("role_mappings_version", [1, 2])
def test_end_to_end_auth_flow_v1(
    conda_store_server,
    testclient,
    authenticate,
    role_mappings_version,
    role,
    permissions,
):
    # Configures authentication
    namespace = f"this-{uuid.uuid4()}"
    other_namespace = f"other-{uuid.uuid4()}"

    conda_store = conda_store_server.conda_store

    authentication = AuthenticationBackend()
    authentication.secret = "supersecret"

    token = authentication.encrypt_token(
        AuthenticationToken(
            primary_namespace=namespace,
            # No default roles
            role_bindings={},
        )
    )

    token_model = authentication.authenticate(token)

    authorization = RBACAuthorizationBackend(
        authentication_db=conda_store.session_factory,
        role_mappings_version=role_mappings_version,
    )

    def authorize():
        return authorization.authorize(
            AuthenticationToken(
                primary_namespace=token_model.primary_namespace,
                role_bindings=token_model.role_bindings,
            ),
            f"{other_namespace}/example-name",
            permissions,
        )

    # No default roles
    assert authorize() is False

    # Creates new namespaces
    for n in (namespace, other_namespace):
        response = testclient.post(f"api/v1/namespace/{n}")
        response.raise_for_status()

    # Deletes roles to start with a clean state
    response = testclient.put(
        f"api/v1/namespace/{namespace}", json={"role_mappings": {}}
    )
    response.raise_for_status()

    # Creates role for 'namespace' with access to 'other_namespace'
    response = testclient.put(
        f"api/v1/namespace/{namespace}",
        json={
            "role_mappings": {
                f"{other_namespace}/ex*-name": [role],
            }
        },
    )
    response.raise_for_status()

    # Should succeed now if v1
    if role_mappings_version == 1:
        assert authorize() is True
    else:
        assert authorize() is False

    # Deletes created roles
    response = testclient.put(
        f"api/v1/namespace/{namespace}", json={"role_mappings": {}}
    )
    response.raise_for_status()

    # Should fail again
    assert authorize() is False


@pytest.mark.parametrize(
    "role, permissions",
    [
        ("viewer", _viewer_permissions),
        ("developer", _editor_permissions),
        ("editor", _editor_permissions),
        ("admin", _admin_permissions),
    ],
)
@pytest.mark.parametrize("role_mappings_version", [1, 2])
def test_end_to_end_auth_flow_v2(
    conda_store_server,
    testclient,
    authenticate,
    role_mappings_version,
    role,
    permissions,
):
    # Configures authentication
    namespace = f"this-{uuid.uuid4()}"
    other_namespace = f"other-{uuid.uuid4()}"

    conda_store = conda_store_server.conda_store

    authentication = AuthenticationBackend()
    authentication.secret = "supersecret"

    token = authentication.encrypt_token(
        AuthenticationToken(
            primary_namespace=namespace,
            # No default roles
            role_bindings={},
        )
    )

    token_model = authentication.authenticate(token)

    authorization = RBACAuthorizationBackend(
        authentication_db=conda_store.session_factory,
        role_mappings_version=role_mappings_version,
    )

    def authorize():
        return authorization.authorize(
            AuthenticationToken(
                primary_namespace=token_model.primary_namespace,
                role_bindings=token_model.role_bindings,
            ),
            f"{other_namespace}/example-name",
            permissions,
        )

    # No default roles
    assert authorize() is False

    # Creates new namespaces
    for n in (namespace, other_namespace):
        response = testclient.post(f"api/v1/namespace/{n}")
        response.raise_for_status()

    # Deletes roles to start with a clean state
    response = testclient.delete(f"api/v1/namespace/{other_namespace}/roles")
    response.raise_for_status()

    # Creates role for 'namespace' with access to 'other_namespace'
    response = testclient.post(
        f"api/v1/namespace/{other_namespace}/role",
        json={"other_namespace": namespace, "role": role},
    )
    response.raise_for_status()

    # Should succeed now if v2
    if role_mappings_version == 2:
        assert authorize() is True
    else:
        assert authorize() is False

    # Deletes created roles
    response = testclient.delete(f"api/v1/namespace/{other_namespace}/roles")
    response.raise_for_status()

    # Should fail again
    assert authorize() is False


@pytest.mark.parametrize(
    "arn_1,arn_2,value",
    [
        ("ab/cd", "a*b/c*d", True),
        ("a1111b/c22222d", "a*b/c*d", True),
        ("a1/cd", "a*b/c*d", False),
        ("abc/ed", "a*b*c/e*d", True),
        ("a111bc/ed", "a*b*c/e*d", True),
        ("a111b2222c/e3333d", "a*b*c/e*d", True),
        ("aaabbbcccc/eeddd", "a*b*c/e*d", True),
        ("aaabbbcccc1/eeddd", "a*b*c/e*d", False),
        ("aaabbbcccc1c/eeddd", "a*b*c/e*d", True),
    ],
)
def test_is_arn_subset(arn_1, arn_2, value):
    assert RBACAuthorizationBackend.is_arn_subset(arn_1, arn_2) == value


@pytest.mark.parametrize(
    # "entity_bindings, new_entity_bindings, authenticated, value",
    "entity_bindings, new_entity_bindings, value",
    [
        # */* viewer is a subset of admin
        (
            {"*/*": ["admin"]},
            {"*/*": ["viewer"]},
            # False,
            True,
        ),
        (
            {"*/*": ["admin"]},
            {"*/*": ["viewer"]},
            # True,
            True,
        ),
        # */* admin is not a subset of viewer
        (
            {"*/*": ["viewer"]},
            {"*/*": ["admin"]},
            # False,
            False,
        ),
        (
            {"*/*": ["viewer"]},
            {"*/*": ["admin"]},
            # True,
            False,
        ),
        # a/b viewer is a subset of admin
        (
            {"a/b": ["admin"]},
            {"a/b": ["viewer"]},
            # False,
            True,
        ),
        (
            {"a/b": ["admin"]},
            {"a/b": ["viewer"]},
            # True,
            True,
        ),
        # a/b admin is not a subset of viewer
        (
            {"a/b": ["viewer"]},
            {"a/b": ["admin"]},
            # False,
            False,
        ),
        (
            {"a/b": ["viewer"]},
            {"a/b": ["admin"]},
            # True,
            False,
        ),
        # default/* vs. */*
        (
            {"*/*": ["viewer"]},
            {"default/*": ["viewer"]},
            # False,
            True,
        ),
        (
            {"*/*": ["viewer"]},
            {"default/*": ["viewer"]},
            # True,
            True,
        ),
        # efault/* vs. d*/*
        (
            {"d*/*": ["viewer"]},
            {"efault/*": ["viewer"]},
            # False,
            False,
        ),
        (
            {"d*/*": ["viewer"]},
            {"efault/*": ["viewer"]},
            # True,
            False,
        ),
        # multiple entities keys
        (
            {"d*/*": ["viewer"], "de*/*": ["admin"]},
            {"default/*": ["developer"]},
            # False,
            True,
        ),
        (
            {"d*/*": ["viewer"], "de*/*": ["admin"]},
            {"default/*": ["developer"]},
            # True,
            True,
        ),
        # multiple entities keys
        (
            {"d*/*": ["viewer"], "de*/*": ["admin"]},
            {"dcefault/*": ["developer"]},
            # False,
            False,
        ),
        (
            {"d*/*": ["viewer"], "de*/*": ["admin"]},
            {"dcefault/*": ["developer"]},
            # True,
            False,
        ),
        # multiple entities keys
        (
            {"d*/*": ["viewer"]},
            {"d*/*": ["viewer"], "dc*/*": ["viewer"]},
            # False,
            True,
        ),
        (
            {"d*/*": ["viewer"]},
            {"d*/*": ["viewer"], "dc*/*": ["viewer"]},
            # True,
            True,
        ),
        # multiple entities keys
        (
            {"d*/*": ["viewer"]},
            {"d*/*": ["viewer"], "dc*/*": ["developer"]},
            # False,
            False,
        ),
        (
            {"d*/*": ["viewer"]},
            {"d*/*": ["viewer"], "dc*/*": ["developer"]},
            # True,
            False,
        ),
    ],
)
def test_is_subset_entity_permissions(
    conda_store,
    entity_bindings,
    new_entity_bindings,
    # authenticated,
    value,
):
    authorization = RBACAuthorizationBackend(
        authentication_db=conda_store.session_factory
    )

    entity = AuthenticationToken(role_bindings=entity_bindings)
    new_entity = AuthenticationToken(role_bindings=new_entity_bindings)

    assert authorization.is_subset_entity_permissions(entity, new_entity) == value
