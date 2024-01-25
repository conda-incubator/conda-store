"""These tests an assumption
`tests/assets/environments/python-flask-env.yaml` is the first
environment added to conda-store.  The given environment has build 1
and has completed building.

List methods cannot be fully tested "exactly" since additional
environments/builds may have been created which would change the
ordering for tests.

"""
import asyncio
import collections
import datetime
import json
import time
import uuid
from functools import partial
from typing import List

import aiohttp
import conda_store_server
import pytest
import requests
from conda_store_server import schema
from pydantic import parse_obj_as

from .conftest import CONDA_STORE_BASE_URL


# Calls APIs that use get_db to ensure DB pool limit is not reached. The default
# queue limit is 15, so this calls a bit more APIs than that. Uses async to call
# APIs as fast as possible, while API handlers are still executing. When we
# reach the pool limit, the old (wrong) behavior was to raise an exception on
# the server side and block on the client side after processing 15 requests. If
# everything works correctly, this test should succeed and not timeout.
#
# The error that used to be thrown on the server side:
# sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached,
# connection timed out, timeout 30.00 (Background on this error at:
# https://sqlalche.me/e/14/3o7r)
#
# https://github.com/conda-incubator/conda-store/issues/598
def test_api_db_pool_queue():
    urls = [
        f"{CONDA_STORE_BASE_URL}api/v1/package",
        f"{CONDA_STORE_BASE_URL}api/v1/namespace/",
        f"{CONDA_STORE_BASE_URL}api/v1/environment/",
        f"{CONDA_STORE_BASE_URL}api/v1/build/",
        f"{CONDA_STORE_BASE_URL}api/v1/channel/",
    ] * 10

    async def get(url, session):
        async with session.get(url) as response:
            r = await response.read()
            print(f"Got {url} with response length {len(r)}")

    async def main(urls):
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            requests = [get(url, session) for url in urls]
            await asyncio.wait_for(asyncio.gather(*requests), timeout=30)
            assert len(requests) == len(urls)
            print(f"Done: processed {len(requests)} requests")

    asyncio.run(main(urls))


def test_api_status_unauth(testclient):
    response = testclient.get("api/v1/")
    response.raise_for_status()

    r = schema.APIGetStatus.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.version == conda_store_server.__version__


def test_api_permissions_unauth(testclient):
    response = testclient.get("api/v1/permission/")
    response.raise_for_status()

    r = schema.APIGetPermission.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.authenticated == False
    assert r.data.primary_namespace == "default"
    assert r.data.entity_permissions == {
        "default/*": sorted([
            schema.Permissions.ENVIRONMENT_READ.value,
            schema.Permissions.NAMESPACE_READ.value,
            schema.Permissions.NAMESPACE_ROLE_MAPPING_READ.value,
        ])
    }


def test_api_permissions_auth(testclient):
    testclient.login()
    response = testclient.get("api/v1/permission/")
    response.raise_for_status()

    r = schema.APIGetPermission.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.authenticated == True
    assert r.data.primary_namespace == "username"
    assert r.data.entity_permissions == {
        "*/*": sorted(
            [
                schema.Permissions.ENVIRONMENT_CREATE.value,
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.ENVIRONMENT_UPDATE.value,
                schema.Permissions.ENVIRONMENT_DELETE.value,
                schema.Permissions.ENVIRONMENT_SOLVE.value,
                schema.Permissions.BUILD_CANCEL.value,
                schema.Permissions.BUILD_DELETE.value,
                schema.Permissions.NAMESPACE_CREATE.value,
                schema.Permissions.NAMESPACE_READ.value,
                schema.Permissions.NAMESPACE_DELETE.value,
                schema.Permissions.NAMESPACE_UPDATE.value,
                schema.Permissions.NAMESPACE_ROLE_MAPPING_CREATE.value,
                schema.Permissions.NAMESPACE_ROLE_MAPPING_READ.value,
                schema.Permissions.NAMESPACE_ROLE_MAPPING_UPDATE.value,
                schema.Permissions.NAMESPACE_ROLE_MAPPING_DELETE.value,
                schema.Permissions.SETTING_READ.value,
                schema.Permissions.SETTING_UPDATE.value,
            ]
        ),
        "default/*": sorted(
            [
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.NAMESPACE_READ.value,
                schema.Permissions.NAMESPACE_ROLE_MAPPING_READ.value,
            ]
        ),
        "filesystem/*": sorted(
            [
                schema.Permissions.ENVIRONMENT_READ.value,
                schema.Permissions.NAMESPACE_READ.value,
                schema.Permissions.NAMESPACE_ROLE_MAPPING_READ.value,
            ]
        ),
    }


def test_api_list_namespace_unauth(testclient):
    response = testclient.get("api/v1/namespace")
    response.raise_for_status()

    r = schema.APIListNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    # by default unauth only has access to the default namespace
    assert len(r.data) == 1


def test_api_list_namespace_auth(testclient):
    testclient.login()
    response = testclient.get("api/v1/namespace")
    response.raise_for_status()

    r = schema.APIListNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    # by default auth has at least two environments created
    # `default` and `filesystem`
    assert len(r.data) >= 2


def test_api_get_namespace_unauth(testclient):
    response = testclient.get("api/v1/namespace/default")
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == "default"


def test_api_get_namespace_unauth_no_exist(testclient):
    response = testclient.get("api/v1/namespace/wrong")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_namespace_auth(testclient):
    testclient.login()
    response = testclient.get("api/v1/namespace/filesystem")
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == "filesystem"


def test_api_get_namespace_auth_no_exist(testclient):
    testclient.login()
    response = testclient.get("api/v1/namespace/wrong")

    assert response.status_code == 404
    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_environments_unauth(testclient):
    response = testclient.get("api/v1/environment")
    response.raise_for_status()

    r = schema.APIListEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_api_list_environments_auth(testclient):
    testclient.login()
    response = testclient.get("api/v1/environment")
    response.raise_for_status()

    r = schema.APIListEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) >= 1


def test_api_get_environment_unauth(testclient):
    response = testclient.get("api/v1/environment/filesystem/python-flask-env")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_environment_auth_existing(testclient):
    testclient.login()
    response = testclient.get("api/v1/environment/filesystem/python-flask-env")
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.namespace.name == "filesystem"
    assert r.data.name == "python-flask-env"


def test_api_get_environment_auth_not_existing(testclient):
    testclient.login()
    response = testclient.get("api/v1/environment/filesystem/wrong")
    assert response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_builds_unauth(testclient):
    response = testclient.get("api/v1/build")
    response.raise_for_status()

    r = schema.APIListBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_api_list_builds_auth(testclient):
    testclient.login()
    response = testclient.get("api/v1/build")
    response.raise_for_status()

    r = schema.APIListBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) >= 1


def test_api_get_build_one_unauth(testclient):
    response = testclient.get("api/v1/build/1")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth(testclient):
    testclient.login()
    response = testclient.get("api/v1/build/1")
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.id == 1
    assert r.data.specification.name == "python-flask-env"
    assert r.data.status == schema.BuildStatus.COMPLETED.value


def test_api_get_build_one_unauth_packages(testclient):
    response = testclient.get("api/v1/build/1/packages")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth_packages(testclient):
    testclient.login()
    response = testclient.get("api/v1/build/1/packages?size=5")
    response.raise_for_status()

    r = schema.APIListCondaPackage.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 5


def test_api_get_build_auth_packages_no_exist(testclient):
    testclient.login()
    response = testclient.get("api/v1/build/101010101/packages")
    assert response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_unauth_logs(testclient):
    response = testclient.get("api/v1/build/1/logs")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_get_build_one_auth_logs(testclient):
    testclient.login()
    response = testclient.get("api/v1/build/1/logs")
    response.raise_for_status()

    logs = response.content.decode("utf-8")
    assert "Preparing transaction:" in logs
    assert "Executing transaction:" in logs


def test_api_get_build_auth_logs_no_exist(testclient):
    testclient.login()
    response = testclient.get("api/v1/build/10101010101/logs")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "url",
    [
        "api/v1/environment/filesystem/python-flask-env/lockfile/",
        "api/v1/environment/filesystem/python-flask-env/conda-lock.yml",
        "api/v1/environment/filesystem/python-flask-env/conda-lock.yaml",
        "api/v1/build/1/lockfile/",
        "api/v1/build/1/conda-lock.yml",
        "api/v1/build/1/conda-lock.yaml",
    ],
)
def test_api_get_build_one_unauth_lockfile(testclient, url):
    response = testclient.get(url)
    assert response.status_code == 403


@pytest.mark.parametrize(
    "url",
    [
        "api/v1/environment/filesystem/python-flask-env/lockfile/",
        "api/v1/environment/filesystem/python-flask-env/conda-lock.yml",
        "api/v1/environment/filesystem/python-flask-env/conda-lock.yaml",
        "api/v1/build/1/lockfile/",
        "api/v1/build/1/conda-lock.yml",
        "api/v1/build/1/conda-lock.yaml",
    ],
)
def test_api_get_build_one_auth_lockfil(testclient, url):
    testclient.login()
    response = testclient.get(url)
    response.raise_for_status()

    lockfile = json.loads(response.content.decode("utf-8"))
    assert "metadata" in lockfile
    assert "package" in lockfile


def test_api_get_build_one_unauth_yaml(testclient):
    response = testclient.get("api/v1/build/1/yaml/")
    assert response.status_code == 403


def test_api_get_build_one_auth_yaml(testclient):
    testclient.login()
    response = testclient.get("api/v1/build/1/yaml/")
    response.raise_for_status()

    environment_yaml = response.content.decode("utf-8")
    assert "name:" in environment_yaml
    assert "channels:" in environment_yaml
    assert "dependencies:" in environment_yaml


def test_api_get_build_two_auth(testclient):
    testclient.login()
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
        "https://conda.anaconda.org/main",
        "https://repo.anaconda.com/pkgs/main",
        "https://conda.anaconda.org/conda-forge",
    }


def test_api_list_conda_packages_unauth(testclient):
    response = testclient.get("api/v1/package?size=15")
    response.raise_for_status()

    r = schema.APIListCondaPackage.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert len(r.data) == 15


# ============ MODIFICATION =============


def test_create_specification_uauth(testclient):
    namespace = "default"
    environment_name = f"pytest-{uuid.uuid4()}"

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


def test_create_specification_auth(testclient):
    namespace = "default"
    environment_name = f"pytest-{uuid.uuid4()}"

    testclient.login()
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


def test_create_specification_parallel_auth(testclient):
    namespace = "default"
    environment_name = f"pytest-{uuid.uuid4()}"

    # Builds different versions to avoid caching
    versions = ["6.2.0", "6.2.1", "6.2.2", "6.2.3", "6.2.4", "6.2.5", "7.1.1", "7.1.2", "7.3.1", "7.4.0"]
    num_builds = len(versions)
    limit_seconds = 60 * 15
    build_ids = collections.deque([])

    # Spins up 'num_builds' builds and adds them to 'build_ids'
    for version in versions:
        testclient.login()
        response = testclient.post(
            "api/v1/specification",
            json={
                "namespace": namespace,
                "specification": json.dumps({
                    "name": environment_name,
                    "channels": ["main"],
                    "dependencies": [f"pytest={version}"],
                }),
            },
            timeout=10,
        )
        response.raise_for_status()
        r = schema.APIPostSpecification.parse_obj(response.json())
        assert r.status == schema.APIStatus.OK
        build_ids.append(r.data.build_id)

    # How long it takes to do a single build
    build_delta = None

    # Checks whether the builds are done (in the order they were scheduled in)
    start = datetime.datetime.now()
    while True:
        # Prints the current build ids in the queue. Visually, if the server is
        # configured to run N jobs in parallel, the queue should have N jobs
        # less almost instantly once the first batch is done processing. After
        # that, the queue should keep shrinking at a steady pace after each of
        # the workers is done
        print("build_ids", build_ids)

        # Checks whether the time limit is reached
        now = datetime.datetime.now()
        delta_seconds = (now - start).total_seconds()
        if delta_seconds > limit_seconds:
            break

        # Measures how long it takes to do a single build
        if build_delta is None and len(build_ids) < num_builds:
            build_delta = delta_seconds

        # Gets the oldest build in the queue as it's the one that's most likely
        # to be done
        try:
            build_id = build_ids.popleft()
        except IndexError:
            break

        # Checks the status
        response = testclient.get(f"api/v1/build/{build_id}", timeout=10)
        response.raise_for_status()
        r = schema.APIGetBuild.parse_obj(response.json())
        assert r.status == schema.APIStatus.OK
        assert r.data.specification.name == environment_name

        # Exit immediately on failure
        assert r.data.status != 'FAILED'

        # If not done, adds the id back to the end of the queue
        if r.data.status != 'COMPLETED':
            build_ids.append(build_id)

        # Adds a small delay to avoid making too many requests too fast. The
        # build takes significantly longer than 1 second, so this shouldn't
        # impact the measurements
        time.sleep(1)

    # Measures how long it took to run the loop
    loop_delta = (datetime.datetime.now() - start).total_seconds()
    print("build_delta", build_delta)
    print("loop_delta", loop_delta)

    # If there are jobs in the queue, the loop didn't complete in the allocated
    # time. So something went wrong, like a build getting stuck or parallel
    # builds not working
    assert len(build_ids) == 0

    # If all jobs are done twice as fast as they would do sequentially, then
    # parallel builds are working
    assert loop_delta < build_delta * (num_builds / 2)


# Only testing size values that will always cause errors. Smaller values could
# cause errors as well, but would be flaky since the test conda-store state
# directory might have different lengths on different systems, for instance,
# due to different username lengths.
@pytest.mark.parametrize(
    "size",
    [
        # minio.error.MinioException: S3 operation failed; code:
        # XMinioInvalidObjectName, message: Object name contains unsupported
        # characters.
        # The error message is misleading: it's a size issue.
        255,
        # SQL error: value too long for type character varying(255)
        256,
    ],
)
def test_create_specification_auth_env_name_too_long(testclient, size):
    namespace = "default"
    environment_name = 'A' * size

    testclient.login()
    response = testclient.post(
        "api/v1/specification",
        json={
            "namespace": namespace,
            "specification": json.dumps({"name": environment_name}),
        },
    )
    if size > 255:
        assert response.status_code == 500
        return  # error, nothing to do
    response.raise_for_status()

    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    build_id = r.data.build_id

    # Try checking that the status is 'FAILED'
    is_updated = False
    for _ in range(5):
        time.sleep(5)

        # check for the given build
        response = testclient.get(f"api/v1/build/{build_id}")
        response.raise_for_status()

        r = schema.APIGetBuild.parse_obj(response.json())
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
        assert False, f"failed to update status"


def test_create_specification_auth_no_namespace_specified(testclient):
    namespace = "username"  # same as login username
    environment_name = f"pytest-{uuid.uuid4()}"

    testclient.login()
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


def test_put_build_trigger_build_noauth(testclient):
    build_id = 1

    response = testclient.put(f"api/v1/build/{build_id}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_put_build_trigger_build_auth(testclient):
    build_id = 1

    testclient.login()
    response = testclient.put(f"api/v1/build/{build_id}")
    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/build/{r.data.build_id}")
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


def test_update_namespace_noauth(testclient):
    namespace = f"filesystem"
    # namespace = f"pytest-{uuid.uuid4()}"

    test_role_mappings = {
        f"{namespace}/*": ["viewer"],
        f"{namespace}/admin": ["admin"],
        f"{namespace}/test": ["admin", "viewer", "developer"],
    }

    # Updates the metadata only
    response = testclient.put(
        f"api/v1/namespace/{namespace}/",
        json={
            "metadata": {"test_key1": "test_value1", "test_key2": "test_value2"},
        },
    )
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR

    # Updates the role mappings only
    response = testclient.put(
        f"api/v1/namespace/{namespace}", json={"role_mappings": test_role_mappings}
    )
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR

    # Updates both the metadata and the role mappings
    response = testclient.put(
        f"api/v1/namespace/{namespace}",
        json={
            "metadata": {"test_key1": "test_value1", "test_key2": "test_value2"},
            "role_mappings": test_role_mappings,
        },
    )
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_update_namespace_auth(testclient):
    namespace = f"filesystem"

    testclient.login()

    test_role_mappings = {
        f"{namespace}/*": ["viewer"],
        f"{namespace}/admin": ["admin"],
        f"{namespace}/test": ["admin", "viewer", "developer"],
    }

    # Updates both the metadata and the role mappings
    response = testclient.put(
        f"api/v1/namespace/{namespace}",
        json={
            "metadata": {"test_key1": "test_value1", "test_key2": "test_value2"},
            "role_mappings": test_role_mappings,
        },
    )

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    # Updates the metadata only
    response = testclient.put(
        f"api/v1/namespace/{namespace}/",
        json={
            "metadata": {"test_key1": "test_value1", "test_key2": "test_value2"},
        },
    )
    response.raise_for_status()

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    # Updates the role mappings only
    response = testclient.put(
        f"api/v1/namespace/{namespace}", json={"role_mappings": test_role_mappings}
    )

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_create_get_delete_namespace_auth(testclient):
    namespace = f"pytest-delete-namespace-{uuid.uuid4()}"

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


def _crud_common(testclient, auth, method, route, params=None, json=None, data_pred=None):
    if auth:
        testclient.login()

    if json is not None:
        response = method(route, json=json)
    elif params is not None:
        response = method(route, params=params)
    else:
        response = method(route)

    if auth:
        response.raise_for_status()
    else:
        assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    if auth:
        assert r.status == schema.APIStatus.OK
        if data_pred is None:
            assert r.data is None
        else:
            assert data_pred(r.data) is True
    else:
        assert r.status == schema.APIStatus.ERROR


@pytest.mark.parametrize("auth", [True, False])
def test_update_namespace_metadata_v2(testclient, auth):
    namespace = f"filesystem"
    make_request = partial(_crud_common, testclient=testclient, auth=auth)

    make_request(
        method=testclient.put,
        route=f"api/v1/namespace/{namespace}/metadata",
        json={"test_key1": "test_value1", "test_key2": "test_value2"},
    )


@pytest.mark.parametrize("auth", [True, False])
def test_crud_namespace_roles_v2(testclient, auth):
    other_namespace = f"pytest-{uuid.uuid4()}"
    namespace = f"filesystem"
    make_request = partial(_crud_common, testclient=testclient, auth=auth)

    # Deletes roles to start with a clean state
    make_request(
        method=testclient.delete,
        route=f"api/v1/namespace/{namespace}/roles",
    )

    # Creates new namespace
    make_request(
        method=testclient.post,
        route=f"api/v1/namespace/{other_namespace}",
    )

    # Creates role for 'other_namespace' with access to 'namespace'
    make_request(
        method=testclient.post,
        route=f"api/v1/namespace/{namespace}/role",
        json={
            "other_namespace": other_namespace,
            "role": "developer"
        },
    )

    # Reads created role
    make_request(
        method=testclient.get,
        route=f"api/v1/namespace/{namespace}/role",
        params={
            "other_namespace": other_namespace,
        },
        data_pred=lambda data: (
            data['namespace'] == 'filesystem' and
            data['other_namespace'] == other_namespace and
            data['role'] == 'developer'
        ),
    )

    # Updates created role
    make_request(
        method=testclient.put,
        route=f"api/v1/namespace/{namespace}/role",
        json={
            "other_namespace": other_namespace,
            "role": "admin"
        },
    )

    # Reads updated roles
    make_request(
        method=testclient.get,
        route=f"api/v1/namespace/{namespace}/roles",
        data_pred=lambda data: (
            data[0]['namespace'] == 'filesystem' and
            data[0]['other_namespace'] == other_namespace and
            data[0]['role'] == 'admin' and
            len(data) == 1
        ),
    )

    # Deletes created role
    make_request(
        method=testclient.delete,
        route=f"api/v1/namespace/{namespace}/role",
        json={
            "other_namespace": other_namespace,
        },
    )

    # Reads roles to check if deleted
    make_request(
        method=testclient.get,
        route=f"api/v1/namespace/{namespace}/roles",
        data_pred=lambda data: data == [],
    )


def test_update_environment_build_unauth(testclient):
    namespace = "filesystem"
    name = "python-flask-env"
    build_id = 1

    response = testclient.put(
        f"api/v1/environment/{namespace}/{name}", json={"build_id": build_id}
    )
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_update_environment_build_auth(testclient):
    namespace = "filesystem"
    name = "python-flask-env"
    build_id = 1

    testclient.login()
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
    assert r.data.current_build_id == 1


def test_delete_environment_unauth(testclient):
    namespace = "filesystem"
    name = "python-flask-env"

    response = testclient.delete(f"api/v1/environment/{namespace}/{name}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_delete_environment_auth(testclient):
    namespace = "default"
    environment_name = f"pytest-delete-environment-{uuid.uuid4()}"

    testclient.login()
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


def test_delete_build_unauth(testclient):
    build_id = 1

    response = testclient.delete(f"api/v1/build/{build_id}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_delete_build_auth(testclient):
    build_id = 1

    testclient.login()
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


def test_api_cancel_build_unauth(testclient):
    build_id = 1

    response = testclient.put(f"api/v1/build/{build_id}/cancel")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_cancel_build_auth(testclient):
    build_id = 1

    testclient.login()
    response = testclient.put(f"api/v1/build/{build_id}")
    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    new_build_id = r.data.build_id

    # Delay to ensure the build kicks off
    build_timeout = 180
    building = False
    start = time.time()
    while time.time() - start < build_timeout:
        try:
            response = testclient.get(f"api/v1/build/{new_build_id}")
        except requests.exceptions.ConnectionError:
            time.sleep(5)
            continue
        response.raise_for_status()

        r = schema.APIGetBuild.parse_obj(response.json())
        assert r.status == schema.APIStatus.OK
        if r.data.status == schema.BuildStatus.BUILDING.value:
            building = True
            break
        time.sleep(5)

    assert building is True

    # The new build should have kicked off, so now we will request to cancel it
    response = testclient.put(f"api/v1/build/{new_build_id}/cancel")
    response.raise_for_status()

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.message == f"build {new_build_id} canceled"

    failed = False
    for _ in range(10):
        # Delay to ensure the build is marked as failed
        time.sleep(5)

        # Ensure status is Failed
        try:
            response = testclient.get(f"api/v1/build/{new_build_id}")
        except requests.exceptions.ConnectionError:
            time.sleep(5)
            continue
        response.raise_for_status()

        r = schema.APIGetBuild.parse_obj(response.json())
        assert r.status == schema.APIStatus.OK
        assert r.data.id == new_build_id
        if r.data.status == schema.BuildStatus.FAILED.value:
            failed = True
            break

    assert failed is True
