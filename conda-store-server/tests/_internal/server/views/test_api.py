# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import contextlib
import datetime
import json
import os
import sys
import time

import httpx
import pytest
import traitlets
import yaml
from fastapi.testclient import TestClient

from conda_store_server import CONDA_STORE_DIR, __version__
from conda_store_server._internal import schema
from conda_store_server._internal.server import dependencies
from conda_store_server._internal.server.pagination import Cursor
from conda_store_server.server import schema as auth_schema


@contextlib.contextmanager
def mock_entity_role_bindings(
    testclient: TestClient,
    role_bindings: auth_schema.RoleBindings,
):
    """Override the entity role bindings for the FastAPI app temporarily.

    Parameters
    ----------
    testclient : TestClient
        FastAPI application for which the entity should be mocked
    role_bindings : auth_schema.RoleBindings
        Role bindings that the mocked entity should have
    """

    def mock_get_entity():
        return auth_schema.AuthenticationToken(role_bindings=role_bindings)

    testclient.app.dependency_overrides[dependencies.get_entity] = mock_get_entity

    yield

    testclient.app.dependency_overrides = {}


def test_deprecation_warning():
    from fastapi.responses import JSONResponse

    from conda_store_server._internal.server.views.api import deprecated

    @deprecated(datetime.date(2024, 12, 17))
    def api_status():
        return JSONResponse(
            status_code=400,
            content={"ok": "ok"},
        )

    result = api_status()
    assert result.headers.get("Deprecation") == "True"
    assert result.headers.get("Sunset") == "Tue, 17 Dec 2024 00:00:00 UTC"


def test_api_version_unauth(testclient):
    response = testclient.get("/api/v1/")
    response.raise_for_status()

    r = schema.APIGetStatus.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.version == __version__


def test_api_permissions_unauth(testclient):
    response = testclient.get("api/v1/permission/")
    response.raise_for_status()

    r = schema.APIGetPermission.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.authenticated is False
    assert r.data.primary_namespace == "default"
    assert r.data.entity_permissions == {
        "default/*": sorted(
            [
                auth_schema.Permissions.ENVIRONMENT_READ.value,
                auth_schema.Permissions.NAMESPACE_READ.value,
                auth_schema.Permissions.NAMESPACE_ROLE_MAPPING_READ.value,
            ]
        )
    }


def test_api_permissions_auth(testclient, authenticate):
    response = testclient.get("api/v1/permission/")
    response.raise_for_status()

    r = schema.APIGetPermission.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.authenticated is True
    assert r.data.primary_namespace == "username"
    assert r.data.entity_permissions == {
        "*/*": sorted(
            [
                auth_schema.Permissions.ENVIRONMENT_CREATE.value,
                auth_schema.Permissions.ENVIRONMENT_READ.value,
                auth_schema.Permissions.ENVIRONMENT_UPDATE.value,
                auth_schema.Permissions.ENVIRONMENT_DELETE.value,
                auth_schema.Permissions.ENVIRONMENT_SOLVE.value,
                auth_schema.Permissions.BUILD_CANCEL.value,
                auth_schema.Permissions.BUILD_DELETE.value,
                auth_schema.Permissions.NAMESPACE_CREATE.value,
                auth_schema.Permissions.NAMESPACE_READ.value,
                auth_schema.Permissions.NAMESPACE_DELETE.value,
                auth_schema.Permissions.NAMESPACE_UPDATE.value,
                auth_schema.Permissions.NAMESPACE_ROLE_MAPPING_CREATE.value,
                auth_schema.Permissions.NAMESPACE_ROLE_MAPPING_READ.value,
                auth_schema.Permissions.NAMESPACE_ROLE_MAPPING_UPDATE.value,
                auth_schema.Permissions.NAMESPACE_ROLE_MAPPING_DELETE.value,
                auth_schema.Permissions.SETTING_READ.value,
                auth_schema.Permissions.SETTING_UPDATE.value,
            ]
        ),
        "default/*": sorted(
            [
                auth_schema.Permissions.ENVIRONMENT_READ.value,
                auth_schema.Permissions.NAMESPACE_READ.value,
                auth_schema.Permissions.NAMESPACE_ROLE_MAPPING_READ.value,
            ]
        ),
        "filesystem/*": sorted(
            [
                auth_schema.Permissions.ENVIRONMENT_READ.value,
                auth_schema.Permissions.NAMESPACE_READ.value,
                auth_schema.Permissions.NAMESPACE_ROLE_MAPPING_READ.value,
            ]
        ),
    }


def test_get_usage_unauth(testclient):
    response = testclient.get("/api/v1/usage/")
    response.raise_for_status()

    r = schema.APIPutSetting.model_validate(response.json())
    assert r.status == schema.APIStatus.OK


def test_get_usage_auth(testclient, authenticate):
    response = testclient.get("/api/v1/usage/")
    response.raise_for_status()

    r = schema.APIPutSetting.model_validate(response.json())
    assert r.status == schema.APIStatus.OK


def test_api_list_namespace_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/namespace")
    response.raise_for_status()

    r = schema.APIListNamespace.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    # by default unauth only has access to the default namespace
    assert len(r.data) == 1
    assert r.data[0].name == "default"


def test_api_list_namespace_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/namespace")
    response.raise_for_status()

    r = schema.APIListNamespace.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert sorted([_.name for _ in r.data]) == ["default", "namespace1", "namespace2"]


def test_api_list_namespace_including_missing_metadata_(
    testclient, seed_namespace_with_edge_cases, authenticate
):
    """Test that a namespace with metadata_ = None can be retrieved.

    See https://github.com/conda-incubator/conda-store/issues/1062
    for additional context.
    """
    response = testclient.get("api/v1/namespace")
    response.raise_for_status()

    r = schema.APIListNamespace.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    namespaces = [_.name for _ in r.data]
    assert "namespace_missing_meta" in namespaces


def test_api_get_namespace_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/namespace/default")
    response.raise_for_status()

    r = schema.APIGetNamespace.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == "default"


def test_api_get_namespace_unauth_no_exist(testclient, seed_conda_store):
    response = testclient.get("api/v1/namespace/namespace1")
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_namespace_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/namespace/namespace1")
    response.raise_for_status()

    r = schema.APIGetNamespace.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == "namespace1"


def test_api_get_namespace_auth_no_exist(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/namespace/wrong")

    assert response.status_code == 404
    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


@pytest.mark.parametrize(
    ("version", "model"),
    [
        ("v1", schema.APIListEnvironment),
        ("v2", schema.APIV2ListEnvironment),
    ],
)
def test_api_list_environments_unauth(testclient, seed_conda_store, version, model):
    response = testclient.get(f"api/{version}/environment")
    response.raise_for_status()

    r = model.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert sorted([_.name for _ in r.data]) == ["name1", "name2"]


@pytest.mark.parametrize(
    ("version", "model"),
    [
        ("v1", schema.APIListEnvironment),
        ("v2", schema.APIV2ListEnvironment),
    ],
)
def test_api_list_environments_auth(
    testclient, seed_conda_store, authenticate, version, model
):
    response = testclient.get(f"api/{version}/environment")
    response.raise_for_status()

    r = model.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert sorted([_.name for _ in r.data]) == ["name1", "name2", "name3", "name4"]


@pytest.mark.parametrize(
    ("requester_role_bindings", "envs_accessible_to_requester"),
    [
        (
            {"*/*": ["viewer"]},
            ["name1", "name2", "name3", "name4"],
        ),
        (
            {"*/*": ["admin"]},
            ["name1", "name2", "name3", "name4"],
        ),
        (
            {"default/*": ["viewer"]},
            ["name1", "name2"],
        ),
        (
            {"namespace1/name3": ["editor"]},
            ["name3"],
        ),
        (
            {"namespace*/*": ["admin"]},
            ["name3", "name4"],
        ),
        (
            {"foo/bar": ["viewer"]},
            [],
        ),
    ],
)
@pytest.mark.parametrize(
    ("target_role_bindings", "envs_accessible_to_target"),
    [
        (
            {"*/name1": ["viewer"]},
            ["name1"],
        ),
        (
            {"default/*": ["viewer"], "e*/e*": ["admin"]},
            ["name1", "name2"],
        ),
        (
            {"namespace1/name3": ["viewer"]},
            ["name3"],
        ),
        (
            {"namespace*/name*": ["viewer"]},
            ["name3", "name4"],
        ),
        (
            {"*/*": ["viewer"]},
            ["name1", "name2", "name3", "name4"],
        ),
    ],
)
def test_api_list_environments_jwt(
    conda_store_server,
    testclient,
    seed_conda_store,
    authenticate,
    target_role_bindings,
    requester_role_bindings,
    envs_accessible_to_target,
    envs_accessible_to_requester,
):
    """Test that the REST API lists the expected environments for a given jwt.

    Since these are authenticated, they also include the default
    role bindings as well.

        {
            "default/*": ["viewer"],
            "filesystem/*": ["viewer"],
        }
    """
    # Update the target and requester envs to include the envs accessible by default
    envs_accessible_to_requester.extend(["name1", "name2"])
    envs_accessible_to_target.extend(["name1", "name2"])

    jwt = conda_store_server.authentication.authentication.encrypt_token(
        auth_schema.AuthenticationToken(role_bindings=target_role_bindings)
    )

    # Override the get_entity dependency to allow the request to appear to be
    # made by the mock entity
    with mock_entity_role_bindings(testclient, requester_role_bindings):
        response = testclient.get(f"api/v1/environment/?jwt={jwt}")

    response.raise_for_status()

    r = schema.APIListEnvironment.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    # The environments returned by `/environment/` should only be the ones
    # visible to both the requesting entity and the target JWT
    assert set(obj.name for obj in r.data) == (
        set(envs_accessible_to_target) & set(envs_accessible_to_requester)
    )


def test_api_get_environment_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/environment/namespace1/name3")
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_environment_auth_existing(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/environment/namespace1/name3")
    response.raise_for_status()

    r = schema.APIGetEnvironment.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.namespace.name == "namespace1"
    assert r.data.name == "name3"


def test_api_get_environment_auth_not_existing(
    testclient, seed_conda_store, authenticate
):
    response = testclient.get("api/v1/environment/namespace1/wrong")
    assert response.status_code == 404

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_builds_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/build")
    response.raise_for_status()

    r = schema.APIListBuild.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 2


def test_api_list_builds_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build")
    response.raise_for_status()

    r = schema.APIListBuild.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 4


def test_api_get_build_one_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/build/3")  # namespace1/name3
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/3")
    response.raise_for_status()

    r = schema.APIGetBuild.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.id == 3
    assert r.data.specification.name == "name3"
    assert r.data.status == schema.BuildStatus.QUEUED.value


def test_api_get_build_one_unauth_packages(testclient, seed_conda_store):
    response = testclient.get("api/v1/build/3/packages")
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth_packages(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/3/packages")
    response.raise_for_status()

    r = schema.APIListCondaPackage.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 1


def test_api_get_build_auth_packages_no_exist(
    testclient, seed_conda_store, authenticate
):
    response = testclient.get("api/v1/build/101010101/packages")
    assert response.status_code == 404

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_unauth_logs(testclient, seed_conda_store):
    response = testclient.get("api/v1/build/3/logs")
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
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

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_conda_channels_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/channel")
    response.raise_for_status()

    r = schema.APIListCondaChannel.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    api_channels = set(_.name for _ in r.data)
    assert api_channels == {
        "https://conda.anaconda.org/conda-forge",
    }


def test_api_list_conda_packages_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/package")
    response.raise_for_status()

    r = schema.APIListCondaPackage.model_validate(response.json())
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

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


# Only testing size values that will always cause errors. Smaller values could
# cause errors as well, but would be flaky since the test conda-store state
# directory might have different lengths on different systems, for instance,
# due to different username lengths.
@pytest.mark.parametrize(
    "size",
    [
        # OSError: [Errno 36] File name too long
        255,
        # OSError: [Errno 36] File name too long
        256,
    ],
)
def test_create_specification_auth_env_name_too_long(
    testclient, celery_worker, authenticate, size
):
    namespace = "default"
    environment_name = "A" * size

    response = testclient.post(
        "api/v1/specification",
        json={
            "namespace": namespace,
            "specification": json.dumps({"name": environment_name}),
        },
    )
    response.raise_for_status()

    r = schema.APIPostSpecification.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    build_id = r.data.build_id

    # Try checking that the status is 'FAILED'
    is_updated = False
    for _ in range(5):
        time.sleep(5)

        # check for the given build
        response = testclient.get(f"api/v1/build/{build_id}")
        response.raise_for_status()

        r = schema.APIGetBuild.model_validate(response.json())
        assert r.status == schema.APIStatus.OK
        assert r.data.specification.name == environment_name
        if r.data.status == "QUEUED":
            continue  # checked too fast, try again
        assert r.data.status == "FAILED"
        assert r.data.status_info == "build_path too long: must be <= 255 characters"
        is_updated = True
        break

    # If we're here, the task didn't update the status on failure
    if not is_updated:
        assert False, "failed to update status"


@pytest.fixture
def win_extended_length_prefix(request):
    # Overrides the attribute before other fixtures are called
    from conda_store_server.app import CondaStore

    assert type(CondaStore.win_extended_length_prefix) is traitlets.Bool
    old_prefix = CondaStore.win_extended_length_prefix
    CondaStore.win_extended_length_prefix = request.param
    yield request.param
    CondaStore.win_extended_length_prefix = old_prefix


@pytest.mark.skipif(sys.platform != "win32", reason="tests a Windows issue")
@pytest.mark.parametrize("win_extended_length_prefix", [True, False], indirect=True)
@pytest.mark.extended_prefix
def test_create_specification_auth_extended_prefix(
    win_extended_length_prefix, testclient, celery_worker, authenticate
):
    # Adds padding to cause an error if the extended prefix is not enabled
    namespace = "default" + "A" * 10
    environment_name = "pytest"

    # The debugpy 1.8.0 package was deliberately chosen because it has long
    # paths internally, which causes issues on Windows due to the path length
    # limit
    response = testclient.post(
        "api/v1/specification",
        json={
            "namespace": namespace,
            "specification": json.dumps(
                {
                    "name": environment_name,
                    "channels": ["conda-forge"],
                    "dependencies": ["debugpy==1.8.0"],
                    "variables": None,
                    "prefix": None,
                    "description": "test",
                }
            ),
        },
        timeout=30,
    )
    response.raise_for_status()

    r = schema.APIPostSpecification.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    build_id = r.data.build_id

    # Try checking that the status is 'FAILED'
    is_updated = False
    for _ in range(30):
        time.sleep(5)

        # check for the given build
        response = testclient.get(f"api/v1/build/{build_id}", timeout=30)
        response.raise_for_status()

        r = schema.APIGetBuild.model_validate(response.json())
        assert r.status == schema.APIStatus.OK
        assert r.data.specification.name == environment_name
        if r.data.status in ("QUEUED", "BUILDING"):
            continue  # checked too fast, try again

        if win_extended_length_prefix:
            assert r.data.status == "COMPLETED"
        else:
            assert r.data.status == "FAILED"
            response = testclient.get(f"api/v1/build/{build_id}/logs", timeout=30)
            response.raise_for_status()
            assert (
                "[WinError 206] The filename or extension is too long" in response.text
            )

        is_updated = True
        break

    # If we're here, the task didn't update the status on failure
    if not is_updated:
        assert False, "failed to update status"


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

    r = schema.APIPostSpecification.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    # check for the given build
    response = testclient.get(f"api/v1/build/{r.data.build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.specification.name == environment_name

    # check for the given environment
    response = testclient.get(f"api/v1/environment/{namespace}/{environment_name}")
    response.raise_for_status()

    r = schema.APIGetEnvironment.model_validate(response.json())
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

    r = schema.APIPostSpecification.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    # check for the given build
    response = testclient.get(f"api/v1/build/{r.data.build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.specification.name == environment_name

    # check for the given environment
    response = testclient.get(f"api/v1/environment/{namespace}/{environment_name}")
    response.raise_for_status()

    r = schema.APIGetEnvironment.model_validate(response.json())
    assert r.data.namespace.name == namespace


def test_put_build_trigger_build_noauth(testclient, seed_conda_store):
    build_id = 3

    response = testclient.put(f"api/v1/build/{build_id}")
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_put_build_trigger_build_auth(
    testclient, seed_conda_store, authenticate, celery_worker
):
    build_id = 1

    response = testclient.put(f"api/v1/build/{build_id}")
    r = schema.APIPostSpecification.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/build/{r.data.build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.model_validate(response.json())
    assert r.status == schema.APIStatus.OK


def test_create_namespace_noauth(testclient):
    namespace = "pytest"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_create_namespace_auth(testclient, authenticate):
    namespace = "pytest"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIAckResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIGetNamespace.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == namespace


def test_create_get_delete_namespace_auth(testclient, celery_worker, authenticate):
    namespace = "pytest-delete-namespace"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIAckResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIGetNamespace.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == namespace

    response = testclient.delete(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIAckResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/namespace/{namespace}")
    assert response.status_code == 404

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_update_environment_build_unauth(testclient, seed_conda_store):
    namespace = "default"
    name = "name1"
    build_id = 1

    response = testclient.put(
        f"api/v1/environment/{namespace}/{name}", json={"build_id": build_id}
    )
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
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

    r = schema.APIAckResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/environment/{namespace}/{name}")
    response.raise_for_status()

    r = schema.APIGetEnvironment.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.current_build_id == 4


def test_delete_environment_unauth(testclient, seed_conda_store):
    namespace = "namespace1"
    name = "name3"

    response = testclient.delete(f"api/v1/environment/{namespace}/{name}")
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
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

    r = schema.APIAckResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.delete(f"api/v1/environment/{namespace}/{environment_name}")
    response.raise_for_status()

    r = schema.APIAckResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.OK


def test_delete_build_unauth(testclient, seed_conda_store):
    build_id = 4

    response = testclient.delete(f"api/v1/build/{build_id}")
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_delete_build_auth(testclient, seed_conda_store, authenticate, celery_worker):
    build_id = 4

    response = testclient.put(f"api/v1/build/{build_id}")
    r = schema.APIPostSpecification.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    new_build_id = r.data.build_id

    response = testclient.get(f"api/v1/build/{new_build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    # currently you cannot delete a build before it succeeds or fails
    # realistically you should be able to delete a build
    response = testclient.delete(f"api/v1/build/{new_build_id}")
    assert response.status_code == 400

    # r = schema.APIAckResponse.model_validate(response.json())
    # assert r.status == schema.APIStatus.OK

    # response = testclient.get(f'api/v1/build/{new_build_id}')
    # assert response.status_code == 404

    # r = schema.APIResponse.model_validate(response.json())
    # assert r.status == schema.APIStatus.ERROR


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/setting/",
        "/api/v1/setting/namespace1/",
        "/api/v1/setting/namespace1/name1",
    ],
)
def test_get_settings_unauth(testclient, route):
    response = testclient.get(route)
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/setting/",
        "/api/v1/setting/namespace1/",
        "/api/v1/setting/namespace1/name1",
    ],
)
def test_put_settings_unauth(testclient, route):
    response = testclient.put(route, json={"conda_included_packages": ["numpy"]})
    assert response.status_code == 403

    r = schema.APIResponse.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/setting/",
        "/api/v1/setting/namespace1/",
        "/api/v1/setting/namespace1/name1",
    ],
)
def test_get_settings_auth(testclient, authenticate, route):
    response = testclient.get(route)
    assert response.status_code == 200

    r = schema.APIGetSetting.model_validate(response.json())
    assert r.status == schema.APIStatus.OK
    assert {
        "default_namespace",
        "filesystem_namespace",
        "default_uid",
        "default_gid",
        "default_permissions",
        "storage_threshold",
        "conda_command",
        "conda_platforms",
        "conda_max_solve_time",
        "conda_indexed_channels",
        "build_artifacts_kept_on_deletion",
        "conda_channel_alias",
        "conda_default_channels",
        "conda_allowed_channels",
        "conda_default_packages",
        "conda_required_packages",
        "conda_included_packages",
        "pypi_default_packages",
        "pypi_required_packages",
        "pypi_included_packages",
        "build_artifacts",
    } <= r.data.keys()


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/setting/",
    ],
)
def test_put_global_settings_auth(testclient, authenticate, route):
    response = testclient.put(
        route,
        json={
            "conda_max_solve_time": 60 * 60,  # 1 hour
        },
    )
    response.raise_for_status()

    r = schema.APIPutSetting.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(route)
    response.raise_for_status()
    r = schema.APIPutSetting.model_validate(response.json())
    assert r.data["conda_max_solve_time"] == 60 * 60


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/setting/",
        "/api/v1/setting/namespace1",
        "/api/v1/setting/namespace1/name1",
    ],
)
def test_put_environment_settings_auth(testclient, authenticate, route):
    response = testclient.put(
        route, json={"conda_included_packages": ["numpy", "ipykernel"]}
    )
    response.raise_for_status()

    r = schema.APIPutSetting.model_validate(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(route)
    response.raise_for_status()
    r = schema.APIPutSetting.model_validate(response.json())
    assert r.data["conda_included_packages"] == ["numpy", "ipykernel"]


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/setting/",
        "/api/v1/setting/namespace1",
        "/api/v1/setting/namespace1/name1",
    ],
)
def test_put_environment_settings_auth_invliad_type(testclient, authenticate, route):
    response = testclient.put(route, json={"conda_included_packages": 1})
    assert response.status_code == 400

    r = schema.APIPutSetting.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR
    assert "validation error" in r.message


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/setting/",
        "/api/v1/setting/namespace1/",
        "/api/v1/setting/namespace1/name1/",
    ],
)
def test_put_settings_auth_invalid_keys(testclient, authenticate, route):
    """This is a test that you cannot set invalid settings"""
    response = testclient.put(
        route,
        json={
            "invalidkey": 1,
            "conda_included_packages": ["numpy"],
        },
    )
    assert response.status_code == 400

    r = schema.APIPutSetting.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR
    assert "Invalid setting keys" in r.message


@pytest.mark.parametrize(
    "route",
    [
        "/api/v1/setting/namespace1",
        "/api/v1/setting/namespace1/name1",
    ],
)
def test_put_global_settings_auth_in_namespace_environment(
    testclient, authenticate, route
):
    """This is a test that you cannot set a global setting at the
    namespace or environment settings level
    """
    response = testclient.put(
        route,
        json={
            "conda_max_solve_time": 60 * 60,  # 1 hour
        },
    )
    assert response.status_code == 400

    r = schema.APIPutSetting.model_validate(response.json())
    assert r.status == schema.APIStatus.ERROR
    assert "global setting" in r.message


def test_default_conda_store_dir():
    # Checks the default value of CONDA_STORE_DIR on different platforms
    dir = str(CONDA_STORE_DIR)
    user = os.environ.get("USER") or os.environ.get("USERNAME")
    if sys.platform == "darwin":
        assert dir == f"/Users/{user}/Library/Application Support/conda-store"
    elif sys.platform == "win32":
        assert dir == rf"C:\Users\{user}\AppData\Local\conda-store\conda-store"
    else:
        assert dir == f"/home/{user}/.local/share/conda-store"


@pytest.mark.parametrize(
    "order",
    [
        "asc",
        "desc",
        None,  # If none is specified, results will be sorted ascending
    ],
)
@pytest.mark.parametrize(
    ("sort_by_param", "attr_func"),
    [
        ("name", lambda x: (x.name, x.id)),
        ("namespace", lambda x: (x.namespace.name, x.id)),
        ("name,namespace", lambda x: (x.name, x.namespace.name, x.id)),
        ("namespace,name", lambda x: (x.namespace.name, x.name, x.id)),
    ],
)
def test_api_list_environments_paginate_order_by(
    conda_store_server,
    testclient,
    seed_conda_store_big,
    authenticate,
    order,
    sort_by_param,
    attr_func,
):
    """Test the REST API lists the paginated envs when given sort_by query parameters."""
    limit = 10
    nfetches = 0
    envs = []

    order_param = "" if order is None else f"&order={order}"
    cursor = None
    cursor_param = ""
    while cursor is None or cursor != Cursor.end():
        response = testclient.get(
            f"api/v2/environment/?limit={limit}&sort_by={sort_by_param}{order_param}{cursor_param}"
        )
        response.raise_for_status()

        model = schema.APIV2ListEnvironment.model_validate(response.json())
        assert model.status == schema.APIStatus.OK

        envs.extend(model.data)

        # Get the next cursor and the next query parameters
        cursor = Cursor.load(model.cursor)
        cursor_param = f"&cursor={model.cursor}"

        nfetches += 1

    env_attrs = [attr_func(env) for env in envs]

    # Check that the number of results reported by the server corresponds to the number of
    # results retrieved
    assert model.count == len(envs)

    # Check that number of results requested corresponds to the number of results retrieved.
    # Since the last fetch isn't always of length `limit`, we subtract off the remainder
    # before checking.
    assert len(envs) - (len(envs) % limit) == limit * (nfetches - 1)

    # The environments should already be sorted; check that this is the case
    assert sorted(env_attrs, reverse=(order == "desc")) == env_attrs


def test_api_list_environments_paginate(
    conda_store_server,
    testclient,
    seed_conda_store_big,
    authenticate,
):
    """Test the REST API lists the envs by id when no query params are specified."""
    limit = 10
    nfetches = 0
    envs = []

    cursor = None
    cursor_param = ""
    while cursor is None or cursor != Cursor.end():
        # breakpoint()
        response = testclient.get(f"api/v2/environment/?limit={limit}{cursor_param}")
        response.raise_for_status()

        model = schema.APIV2ListEnvironment.model_validate(response.json())
        assert model.status == schema.APIStatus.OK

        envs.extend(model.data)

        # Get the next cursor and the next query parameters
        cursor = Cursor.load(model.cursor)
        cursor_param = f"&cursor={model.cursor}"

        nfetches += 1

    env_ids = [env.id for env in envs]

    # Check that the number of results reported by the server corresponds to the number of
    # results retrieved
    assert model.count == len(env_ids)

    # Check that number of results requested corresponds to the number of results retrieved.
    # Since the last fetch isn't always of length `limit`, we subtract off the remainder
    # before checking.
    assert len(env_ids) - (len(env_ids) % limit) == limit * (nfetches - 1)

    # Check that the environments are sorted by ID
    assert sorted(env_ids) == env_ids


def test_api_list_environments_invalid_query_params(
    conda_store_server,
    testclient,
    seed_conda_store_big,
    authenticate,
):
    """Test that invalid query parameters return 400 status codes."""
    response = testclient.get("api/v2/environment/?order=foo")
    with pytest.raises(httpx.HTTPStatusError):
        response.raise_for_status()

    response = testclient.get("api/v2/environment/?sort_by=foo")
    with pytest.raises(httpx.HTTPStatusError):
        response.raise_for_status()
