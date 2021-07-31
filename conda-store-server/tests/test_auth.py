import pytest
import datetime

from conda_store_server.server.auth import (
    AuthenticationBackend,
    RBACAuthorizationBackend,
    Permissions,
)
from conda_store_server.schema import AuthenticationToken


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
def test_authorization(entity_bindings, arn, permissions, authorized):
    authorization = RBACAuthorizationBackend()
    assert authorized == authorization.authorize(entity_bindings, arn, permissions)


def test_end_to_end_auth_flow():
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

    authorization = RBACAuthorizationBackend()
    assert authorization.authorize(
        token_model.role_bindings,
        "example-namespace/example-name",
        {
            Permissions.ENVIRONMENT_DELETE,
            Permissions.ENVIRONMENT_READ,
        },
        authenticated=True,
    )
