"""Helper functions for user journeys."""
from datetime import datetime, timedelta, timezone
from enum import Enum

import requests

TIMEOUT = 10


class APIBuildStatus(Enum):
    """Enum for API build status."""
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED = "QUEUED"
    BUILDING = "BUILDING"


class APIHelper:
    """
        Helper class for making requests to the API.
        These methods are used to build tests for user journeys
    """

    def __init__(self,
                 base_url: str, token: str = "",
                 username: str = "username", password: str = "password"
                 ) -> None:
        self.base_url = base_url
        self.token = token
        if not token:
            # Log in if no token is provided to set the token
            self._login(username, password)

    def make_request(
            self,  endpoint: str, method: str = "GET", json_data: dict = None,
            headers: dict = None, timeout: int = TIMEOUT) -> requests.Response:
        """ Make a request to the API. """
        url = f"{self.base_url}/{endpoint}"
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.token}"
        response = requests.request(
            method, url, json=json_data, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response

    def _login(self, username: str, password: str) -> None:
        """ Log in to the API and set an access token."""
        json_data = {"username": username, "password": password}
        response = requests.post(
            f"{self.base_url}/login", json=json_data, timeout=TIMEOUT)
        cookies = response.cookies.get_dict()
        token_response = requests.post(
            f"{self.base_url}/api/v1/token", cookies=cookies, timeout=TIMEOUT)
        data = token_response.json()
        self.token = data["data"]["token"]


def get_current_time() -> datetime:
    """ Get the current time. """
    return datetime.now(timezone.utc)


def get_time_in_future(hours: int) -> datetime:
    """ Get the time in the future."""
    current_time = get_current_time()
    future_time = current_time + timedelta(hours=hours)
    return future_time


def get_iso8601_time(hours: int) -> str:
    """ Get the time in the future in ISO 8601 format. """
    future_time = get_time_in_future(hours)
    iso_format = future_time.isoformat()
    return iso_format


def create_namespace(api: APIHelper, namespace: str) -> requests.Response:
    """ Create a namespace. """
    return api.make_request(
        f"api/v1/namespace/{namespace}", method="POST")


def create_token(
        api: APIHelper, namespace: str, role: str,
        default_namespace: str = "default"
        ) -> requests.Response:
    """ Create a token with a specified role in a specified namespace. """
    one_hour_in_future = get_time_in_future(1)
    json_data = {
        "primary_namespace": default_namespace,
        "expiration": one_hour_in_future.isoformat(),
        "role_bindings": {
            f"{namespace}/*": [role]
        }
    }
    return api.make_request(
        "api/v1/token", method="POST", json_data=json_data)


def create_environment(
        api: APIHelper,  namespace: str, specification_path: str
        ) -> requests.Response:
    """
        Create an environment.
        The environment specification is read
        from a conda environment.yaml file.
    """
    with open(specification_path, "r", encoding="utf-8") as file:
        specification_content = file.read()

    json_data = {
        "namespace": namespace,
        "specification": specification_content
    }

    return api.make_request(
        "api/v1/specification", method="POST", json_data=json_data)


def wait_for_successful_build(
        api: APIHelper, build_id: str
        ) -> requests.Response:
    """ Wait for a build to complete."""
    status = APIBuildStatus.QUEUED.value
    while status != APIBuildStatus.COMPLETED.value:
        response = api.make_request(
            f"api/v1/build/{build_id}", method="GET")
        status = response.json()["data"]["status"]
        if status == APIBuildStatus.FAILED.value:
            raise AssertionError("Build failed")
    return response


def delete_environment(
        api: APIHelper, namespace: str, environment_name: str
        ) -> requests.Response:
    """ Delete an environment."""
    return api.make_request(
        f"api/v1/environment/{namespace}/{environment_name}",
        method="DELETE")


def delete_namespace(api: APIHelper, namespace: str) -> requests.Response:
    """ Delete a namespace."""
    return api.make_request(f"api/v1/namespace/{namespace}", method="DELETE")