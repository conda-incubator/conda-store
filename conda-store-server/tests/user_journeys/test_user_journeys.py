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
    namespace = utils.API.gen_random_namespace()
    api = utils.API(base_url=base_url, token=token)
    api.create_namespace(namespace)
    response = api.create_environment(namespace, specification_path)
    data = response.json()["data"]
    assert "build_id" in data
    build_id = data["build_id"]
    assert build_id is not None
    build = api.wait_for_successful_build(build_id)
    environment_name = build.json()["data"]["specification"]["name"]
    api.delete_environment(namespace, environment_name)
    api.delete_namespace(namespace)
