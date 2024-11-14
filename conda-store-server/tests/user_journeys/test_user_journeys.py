# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""User journey tests for the API."""

import os

import pytest
import utils.api_utils as utils


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get the base URL for the API."""
    base = os.getenv("CONDA_STORE_BASE_URL", "http://localhost:8080")
    return f"{base}/conda-store"


@pytest.fixture(scope="session")
def token(base_url) -> str:
    """Get the token for the API."""
    return os.getenv("CONDA_STORE_TOKEN", "")


@pytest.mark.user_journey
@pytest.mark.parametrize(
    "specification_path",
    [
        ("tests/user_journeys/test_data/simple_environment.yaml"),
    ],
)
def test_admin_user_can_create_environment(
    base_url: str, token: str, specification_path: str
) -> None:
    """Test that an admin user can create an environment."""
    api = utils.API(base_url=base_url, token=token)
    namespace = "default"
    environment = api.create_environment(namespace, specification_path).json()["data"][
        "specification"
    ]["name"]
    api.delete_environment(namespace, environment)


@pytest.mark.user_journey
@pytest.mark.parametrize(
    "specification_path",
    [
        ("tests/user_journeys/test_data/simple_environment.yaml"),
    ],
)
def test_admin_login_and_delete_shared_environment(
    base_url: str, specification_path: str
) -> None:
    """Test that an admin can login and create/delete an env in a shared namespace."""
    api = utils.API(base_url=base_url)

    # Create a shared namespace; default permissions for namepace/environment
    # */* is admin
    namespace = api.create_namespace().json()["data"]["name"]
    environment = api.create_environment(
        namespace,
        specification_path,
    ).json()["data"]["specification"]["name"]

    api.delete_environment(namespace, environment)
    api.delete_namespace(namespace)


@pytest.mark.user_journey
@pytest.mark.parametrize(
    "specification_path",
    [
        ("tests/user_journeys/test_data/simple_environment.yaml"),
    ],
)
def test_user_login_and_create_shared_environment(
    base_url: str, specification_path: str
) -> None:
    """Test that a user can login and create an environment in a shared namespace."""
    api = utils.API(base_url=base_url)

    # Create a shared namespace; default permissions for namepace/environment
    # */* is admin
    namespace = api.create_namespace().json()["data"]["name"]

    dev_api = utils.API(
        base_url=base_url,
        token=api.create_token(
            namespace,
            "developer",
        ).json()["data"]["token"],
    )

    environment = dev_api.create_environment(
        namespace,
        specification_path,
    ).json()["data"]["specification"]["name"]

    api.delete_environment(namespace, environment)
    api.delete_namespace(namespace)


@pytest.mark.user_journey
def test_admin_set_active_build(base_url: str):
    """Test that an admin can delete environments."""
    specs = [
        "tests/user_journeys/test_data/simple_environment.yaml",
        "tests/user_journeys/test_data/simple_environment2.yaml",
    ]
    api = utils.API(base_url=base_url)
    namespace = api.create_namespace().json()["data"]["name"]
    envs = set()
    for spec in specs:
        envs.add(
            api.create_environment(namespace, spec).json()["data"]["specification"][
                "name"
            ]
        )

    environment = list(envs)[0]
    builds = api.get_builds(
        namespace=namespace,
        environment=environment,
    )

    # The environment in the two specs has the same name, so there should be
    # two builds for this environment in this namespace
    assert len(builds) == 2

    build_ids = [build["id"] for build in builds]

    assert api.get_environment(
        namespace=namespace,
        environment=environment,
    )["current_build_id"] == max(build_ids)

    api.set_active_build(
        namespace=namespace, environment=environment, build_id=min(build_ids)
    )

    assert api.get_environment(
        namespace=namespace,
        environment=environment,
    )["current_build_id"] == min(build_ids)

    for env in envs:
        api.delete_environment(namespace, env)
    api.delete_namespace(namespace)


@pytest.mark.user_journey
def test_failed_build_logs(base_url: str):
    """Test that a user can access logs for a failed build."""
    api = utils.API(base_url=base_url)
    namespace = "default"
    build_request = api.create_environment(
        namespace,
        "tests/user_journeys/test_data/broken_environment.yaml",
    ).json()

    assert build_request["data"]["status"] == "FAILED"
    assert (
        "invalidpackagenamefaasdfagksdjfhgaskdf"
        in api.get_logs(build_request["data"]["id"]).text
    )

    api.delete_environment(
        namespace,
        build_request["data"]["specification"]["name"],
    )


@pytest.mark.user_journey
def test_cancel_build(base_url: str):
    """Test that a user cancel a build in progress."""
    api = utils.API(base_url=base_url)
    namespace = "default"
    build_id = api.create_environment(
        namespace,
        "tests/user_journeys/test_data/complicated_environment.yaml",
        wait=False,
    ).json()["data"]["build_id"]

    assert api.get_build_status(build_id) in [
        utils.BuildStatus.QUEUED,
        utils.BuildStatus.BUILDING,
    ]
    api.cancel_build(build_id)

    def check_status():
        status = api.get_build_status(build_id)
        if status in [utils.BuildStatus.QUEUED, utils.BuildStatus.BUILDING]:
            return False

        if status in [utils.BuildStatus.COMPLETED, utils.BuildStatus.FAILED]:
            raise ValueError(
                f"Build {build_id} {status.value.lower()}, but should have been canceled."
            )

        return status == utils.BuildStatus.CANCELED

    utils.wait_for_condition(check_status, timeout=60, interval=1)


@pytest.mark.user_journey
def test_get_lockfile(base_url: str):
    """Test that an admin can access a valid lockfile for a build."""
    api = utils.API(base_url=base_url)
    namespace = "default"
    build_request = api.create_environment(
        namespace,
        "tests/user_journeys/test_data/simple_environment.yaml",
    ).json()

    lockfile = api.get_lockfile(build_request["data"]["id"])

    packages = set(package["name"] for package in lockfile["package"])
    assert "python" in packages
    assert "fastapi" in packages

    api.delete_environment(namespace, build_request["data"]["specification"]["name"])
