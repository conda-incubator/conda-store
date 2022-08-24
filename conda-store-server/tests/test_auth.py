import pytest
import datetime

from conda_store_server.server.auth import (
    AuthenticationBackend,
    RBACAuthorizationBackend,
)
from conda_store_server.schema import AuthenticationToken, Permissions


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
    "entity_bindings, new_entity_bindings, authenticated, value",
    [
        # */* viewer is a subset of admin
        ({"*/*": ["admin"]}, {"*/*": ["viewer"]}, False, True),
        ({"*/*": ["admin"]}, {"*/*": ["viewer"]}, True, True),
        # */* admin is not a subset of viewer
        ({"*/*": ["viewer"]}, {"*/*": ["admin"]}, False, False),
        ({"*/*": ["viewer"]}, {"*/*": ["admin"]}, True, False),
        # a/b viewer is a subset of admin
        ({"a/b": ["admin"]}, {"a/b": ["viewer"]}, False, True),
        ({"a/b": ["admin"]}, {"a/b": ["viewer"]}, True, True),
        # a/b admin is not a subset of viewer
        ({"a/b": ["viewer"]}, {"a/b": ["admin"]}, False, False),
        ({"a/b": ["viewer"]}, {"a/b": ["admin"]}, True, False),
        # default/* vs. */*
        ({"*/*": ["viewer"]}, {"default/*": ["viewer"]}, False, True),
        ({"*/*": ["viewer"]}, {"default/*": ["viewer"]}, True, True),
        # efault/* vs. d*/*
        ({"d*/*": ["viewer"]}, {"efault/*": ["viewer"]}, False, False),
        ({"d*/*": ["viewer"]}, {"efault/*": ["viewer"]}, True, False),
        # multiple entities keys
        (
            {"d*/*": ["viewer"], "de*/*": ["admin"]},
            {"default/*": ["developer"]},
            False,
            True,
        ),
        (
            {"d*/*": ["viewer"], "de*/*": ["admin"]},
            {"default/*": ["developer"]},
            True,
            True,
        ),
        # multiple entities keys
        (
            {"d*/*": ["viewer"], "de*/*": ["admin"]},
            {"dcefault/*": ["developer"]},
            False,
            False,
        ),
        (
            {"d*/*": ["viewer"], "de*/*": ["admin"]},
            {"dcefault/*": ["developer"]},
            True,
            False,
        ),
        # multiple entities keys
        ({"d*/*": ["viewer"]}, {"d*/*": ["viewer"], "dc*/*": ["viewer"]}, False, True),
        ({"d*/*": ["viewer"]}, {"d*/*": ["viewer"], "dc*/*": ["viewer"]}, True, True),
        # multiple entities keys
        (
            {"d*/*": ["viewer"]},
            {"d*/*": ["viewer"], "dc*/*": ["developer"]},
            False,
            False,
        ),
        (
            {"d*/*": ["viewer"]},
            {"d*/*": ["viewer"], "dc*/*": ["developer"]},
            True,
            False,
        ),
    ],
)
def test_is_subset_entity_permissions(
    entity_bindings, new_entity_bindings, authenticated, value
):
    authorization = RBACAuthorizationBackend()
    assert (
        authorization.is_subset_entity_permissions(
            entity_bindings, new_entity_bindings, authenticated
        )
        == value
    )
