"""User journey tests for the API."""
import os
import uuid

import pytest
from helpers import helpers as h


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
@pytest.mark.parametrize("filename", [
    ("tests/user_journeys/test_data/simple_environment.yaml"),
    # ("test_data/complex-environment.yaml")
    ])
def test_admin_user_can_create_environment(base_url, token, filename) -> None:
    """Test that an admin user can create an environment."""
    namespace = uuid.uuid4().hex  # Generate a random namespace
    print(os.path.abspath(filename))
    api = h.APIHelper(base_url=base_url, token=token)
    specification_path = f"{filename}"
    response = h.create_environment(api, namespace, specification_path)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "build_id" in data
    build_id = data["build_id"]
    assert build_id is not None
    build = h.wait_for_successful_build(api, build_id)
    environment_name = build.json()["data"]["specification"]["name"]
    h.delete_environment(api, namespace, environment_name)
    h.delete_namespace(api, namespace)
