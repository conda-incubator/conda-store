import datetime
import inspect
import json
import time

import celery
import pytest
import yaml
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
                schema.Permissions.NAMESPACE_UPDATE.value,
                schema.Permissions.NAMESPACE_ROLE_MAPPING_CREATE.value,
                schema.Permissions.NAMESPACE_ROLE_MAPPING_DELETE.value,
                schema.Permissions.SETTING_READ.value,
                schema.Permissions.SETTING_UPDATE.value,
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


def test_get_usage_unauth(testclient):
    response = testclient.get("/api/v1/usage/")
    response.raise_for_status()

    r = schema.APIPutSetting.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_get_usage_auth(testclient, authenticate):
    response = testclient.get("/api/v1/usage/")
    response.raise_for_status()

    r = schema.APIPutSetting.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


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

    environment_yaml = yaml.safe_load(response.content.decode("utf-8"))
    assert {"name", "channels", "dependencies"} <= environment_yaml.keys()


def test_api_get_build_two_auth(testclient, seed_conda_store, authenticate):
    response = testclient.get("api/v1/build/1010101010101")
    response.status_code == 404

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_api_list_conda_channels_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/channel")
    response.raise_for_status()

    r = schema.APIListCondaChannel.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    api_channels = set(_.name for _ in r.data)
    assert api_channels == {
        "https://conda.anaconda.org/conda-forge",
    }


def test_api_list_conda_packages_unauth(testclient, seed_conda_store):
    response = testclient.get("api/v1/package")
    response.raise_for_status()

    r = schema.APIListCondaPackage.parse_obj(response.json())
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

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


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


def test_put_build_trigger_build_noauth(testclient, seed_conda_store):
    build_id = 3

    response = testclient.put(f"api/v1/build/{build_id}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_put_build_trigger_build_auth(
    testclient, seed_conda_store, authenticate, celery_worker
):
    build_id = 1

    response = testclient.put(f"api/v1/build/{build_id}")
    r = schema.APIPostSpecification.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/build/{r.data.build_id}")
    response.raise_for_status()

    r = schema.APIGetBuild.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


CREATE_BUILD_DELAY_SECS=30
CREATE_BUILD_NUM_BUILDS=4


# To test concurrent builds, we overwrite the 'build_conda_environment'
# function, which is used in 'create_build', such that it always takes N
# seconds, with the expectation that M concurrent calls will execute faster than
# M sequential calls. If concurrency works, the test should take roughly N
# seconds, plus some small overhead. If it doesn't work, it should take M * N
# seconds. Since no actual build is performed, we also need to overwrite other
# functions that are called from tasks started by the PUT request for
# 'create_build'.
#
# Note: this is a fixture to have control over fixture execution order. We need
# to run this before celery worker code starts executing.
@pytest.fixture
def mock_create_build(mocker):
    def mock_build_conda_environment(*args, **kwargs):
        # The print is here to make it easier to see that we're actually calling
        # this mock function.
        print(f"Running {inspect.currentframe().f_code.co_name}")
        # Inserts delay
        time.sleep(CREATE_BUILD_DELAY_SECS)

    mocker.patch('conda_store_server.worker.tasks.build_conda_environment',
                 new=mock_build_conda_environment)
    mocker.patch('conda_store_server.worker.tasks.build_conda_env_export',
                 new=lambda *args, **kwargs: None)
    mocker.patch('conda_store_server.worker.tasks.build_conda_pack',
                 new=lambda *args, **kwargs: None)
    mocker.patch('conda_store_server.worker.tasks.build_conda_docker',
                 new=lambda *args, **kwargs: None)


# The following 'parametrize' calls set parameters used by the 'celery_worker'
# fixture, so that it runs concurrently.
#
# Depending on whether code is run as an app or via pytest, celery defaults
# might be different. We need to make sure that parameters responsible for
# concurrent execution are set properly and that they match our app's defaults,
# so that we're testing the same configuration our app would run with.
#
# TODO: This doesn't read values from our app's config file. Instead, the test
# assumes that these are the same as the celery defaults.
#
# With pytest, the defaults in 'start_worker' (as of celery 5.3.1) are:
# concurrency=1 and pool='solo', which means non-concurrent execution.
#
# This shows defaults outside of pytest:
# >>> from celery import Celery
# >>> c = Celery()
# >>> print(c.conf['worker_concurrency'])
# None
# >>> print(c.conf['worker_pool'])
# prefork
#
# This shows all available pools:
# >>> from celery import concurrency
# >>> concurrency.get_available_pool_names()
# ('prefork', 'eventlet', 'gevent', 'solo', 'processes', 'threads', 'custom')
#
# https://stackoverflow.com/questions/66177414/run-celery-tasks-concurrently-using-pytest
# https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#override-a-fixture-with-direct-test-parametrization
@pytest.mark.parametrize("celery_worker_parameters", [{"concurrency": CREATE_BUILD_NUM_BUILDS}])
@pytest.mark.parametrize("celery_worker_pool", ["prefork"])
def test_put_build_trigger_build_auth_concurrency(
    testclient, seed_conda_store, authenticate, mock_create_build, celery_worker
):
    start_time = datetime.datetime.utcnow()

    init_build_id = 1
    tasks = celery.result.ResultSet([])
    for _ in range(CREATE_BUILD_NUM_BUILDS):
        # Starts build
        response = testclient.put(f"api/v1/build/{init_build_id}")
        # Checks that response is OK
        r = schema.APIPostSpecification.parse_obj(response.json())
        assert r.status == schema.APIStatus.OK
        # Gets task for this build
        task = celery_worker.app.AsyncResult(f"build-{r.data.build_id}-environment")
        tasks.add(task)
    # Waits for tasks to finish
    tasks.join()

    # Checks test execution time
    end_time = datetime.datetime.utcnow()
    time_delta = end_time - start_time
    # Makes sure our code is actually executing (at least N seconds)
    assert time_delta >= datetime.timedelta(seconds=CREATE_BUILD_DELAY_SECS)
    # Makes sure code runs concurrently (N seconds + some overhead)
    assert time_delta < datetime.timedelta(seconds=CREATE_BUILD_DELAY_SECS * 2)


def test_create_namespace_noauth(testclient):
    namespace = "pytest"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_create_namespace_auth(testclient, authenticate):
    namespace = "pytest"

    response = testclient.post(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/namespace/{namespace}")
    response.raise_for_status()

    r = schema.APIGetNamespace.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.name == namespace


def test_create_get_delete_namespace_auth(testclient, celery_worker, authenticate):
    namespace = "pytest-delete-namespace"

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


def test_update_environment_build_unauth(testclient, seed_conda_store):
    namespace = "default"
    name = "name1"
    build_id = 1

    response = testclient.put(
        f"api/v1/environment/{namespace}/{name}", json={"build_id": build_id}
    )
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
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

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(f"api/v1/environment/{namespace}/{name}")
    response.raise_for_status()

    r = schema.APIGetEnvironment.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK
    assert r.data.current_build_id == 4


def test_delete_environment_unauth(testclient, seed_conda_store):
    namespace = "namespace1"
    name = "name3"

    response = testclient.delete(f"api/v1/environment/{namespace}/{name}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
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

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.delete(f"api/v1/environment/{namespace}/{environment_name}")
    response.raise_for_status()

    r = schema.APIAckResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK


def test_delete_build_unauth(testclient, seed_conda_store):
    build_id = 4

    response = testclient.delete(f"api/v1/build/{build_id}")
    assert response.status_code == 403

    r = schema.APIResponse.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR


def test_delete_build_auth(testclient, seed_conda_store, authenticate, celery_worker):
    build_id = 4

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


def test_prometheus_metrics(testclient):
    response = testclient.get("metrics")
    d = {
        line.split()[0]: line.split()[1]
        for line in response.content.decode("utf-8").split("\n")
    }
    assert {
        "conda_store_disk_free",
        "conda_store_disk_total",
        "conda_store_disk_usage",
    } <= d.keys()


def test_celery_stats(testclient, celery_worker):
    response = testclient.get("celery")
    assert response.json().keys() == {
        "active_tasks",
        "availability",
        "registered_tasks",
        "scheduled_tasks",
        "stats",
    }


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

    r = schema.APIResponse.parse_obj(response.json())
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

    r = schema.APIResponse.parse_obj(response.json())
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

    r = schema.APIGetSetting.parse_obj(response.json())
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
        "default_docker_base_image",
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

    r = schema.APIPutSetting.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(route)
    response.raise_for_status()
    r = schema.APIPutSetting.parse_obj(response.json())
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

    r = schema.APIPutSetting.parse_obj(response.json())
    assert r.status == schema.APIStatus.OK

    response = testclient.get(route)
    response.raise_for_status()
    r = schema.APIPutSetting.parse_obj(response.json())
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

    r = schema.APIPutSetting.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR
    assert "Invalid parsing" in r.message


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

    r = schema.APIPutSetting.parse_obj(response.json())
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
    namespace or environment settings level"""
    response = testclient.put(
        route,
        json={
            "conda_max_solve_time": 60 * 60,  # 1 hour
        },
    )
    assert response.status_code == 400

    r = schema.APIPutSetting.parse_obj(response.json())
    assert r.status == schema.APIStatus.ERROR
    assert "global setting" in r.message
