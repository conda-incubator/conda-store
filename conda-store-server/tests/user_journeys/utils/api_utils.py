# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Helper functions for user journeys."""

import json
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union

import requests

import utils.time_utils as time_utils

TIMEOUT = 10


class BuildStatus(Enum):
    """Enum for API build status."""

    QUEUED = "QUEUED"
    BUILDING = "BUILDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class NamespaceStatus(Enum):
    OK = "ok"
    ERROR = "error"


class API:
    """
    Helper class for making requests to the API.
    These methods are used to build tests for user journeys
    """

    def __init__(
        self,
        base_url: str,
        token: str = "",
        username: str = "username",
        password: str = "password",
    ) -> None:
        self.base_url = base_url
        self.token = token
        if not token:
            # Log in if no token is provided to set the token
            self._login(username, password)

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        json_data: dict = None,
        headers: dict = None,
        timeout: int = TIMEOUT,
    ) -> requests.Response:
        """Make a request to the API."""
        url = f"{self.base_url}/{endpoint}"
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.token}"
        response = requests.request(
            method, url, json=json_data, headers=headers, timeout=timeout
        )
        response.raise_for_status()
        return response

    def get_logs(self, build_id: int) -> requests.Response:
        """Get the logs for the given build id.

        Parameters
        ----------
        build_id : int
            ID of the build to get the logs for

        Returns
        -------
        requests.Response
            Response from the conda-store-server. Logs are stored in the
            `.text` property, i.e. response.json()['text']
        """
        return self._make_request(f"api/v1/build/{build_id}/logs/")

    def _login(self, username: str, password: str) -> None:
        """Log in to the API and set an access token."""
        json_data = {"username": username, "password": password}
        response = requests.post(
            f"{self.base_url}/login", json=json_data, timeout=TIMEOUT
        )
        cookies = response.cookies.get_dict()
        token_response = requests.post(
            f"{self.base_url}/api/v1/token", cookies=cookies, timeout=TIMEOUT
        )
        data = token_response.json()
        self.token = data["data"]["token"]

    def create_namespace(self, namespace: Union[str, None] = None) -> requests.Response:
        """Create a namespace.

        Parameters
        ----------
        namespace : str
            Name of the namespace to create. If None, use a random namespace name

        Returns
        -------
        requests.Response
            Response from the conda-store server
        """
        if namespace is None:
            namespace = self.gen_random_namespace()

        self._make_request(f"api/v1/namespace/{namespace}", method="POST")
        return self._make_request(f"api/v1/namespace/{namespace}")

    def create_token(
        self, namespace: str, role: str, default_namespace: str = "default"
    ) -> requests.Response:
        """Create a token with a specified role in a specified namespace."""
        json_data = {
            "primary_namespace": default_namespace,
            "expiration": time_utils.get_iso8601_time(1),
            "role_bindings": {f"{namespace}/*": [role]},
        }
        return self._make_request("api/v1/token", method="POST", json_data=json_data)

    def create_environment(
        self,
        namespace: str,
        specification_path: str,
        max_iterations: int = 100,
        sleep_time: int = 5,
        wait: bool = True,
    ) -> requests.Response:
        """Create an environment.

        Parameters
        ----------
        namespace : str
            Namespace the environment should be written to
        specification_path : str
            Path to conda environment specification file
        max_iterations : int
            Max number of times to check whether the build completed before failing
        sleep_time : int
            Seconds to wait between each status check
        wait : bool
            If True, wait for the build to complete, fail, or be canceled before
            returning a response. If False, return the response from the specification
            POST immediately without waiting

        Returns
        -------
        requests.Response
            Response from the conda-store server's api/v1/build/{build_id}/
            endpoint
        """
        with open(specification_path, encoding="utf-8") as file:
            specification_content = file.read()

        response = self._make_request(
            "api/v1/specification",
            method="POST",
            json_data={"namespace": namespace, "specification": specification_content},
        )
        if not wait:
            return response

        build_id = response.json()["data"]["build_id"]

        def check_status():
            status = self.get_build_status(build_id)
            if status in [BuildStatus.QUEUED, BuildStatus.BUILDING]:
                return False
            return status in [
                BuildStatus.FAILED,
                BuildStatus.CANCELED,
                BuildStatus.COMPLETED,
            ]

        wait_for_condition(check_status, timeout=240, interval=1)
        return self._make_request(f"api/v1/build/{build_id}/")

    def delete_environment(
        self, namespace: str, environment_name: str
    ) -> requests.Response:
        """Delete an environment."""
        return self._make_request(
            f"api/v1/environment/{namespace}/{environment_name}", method="DELETE"
        )

    def list_environments(self, namespace: Optional[str] = None):
        """List the environments in the given namespace.

        Parameters
        ----------
        namespace : Optional[str]
            Name of the namespace for which environments are to be retrieved.
            If None, all environments are retrieved.

        Returns
        -------
        requests.Response
            Response from the server containing the list of environments
        """
        if namespace:
            return self._make_request(
                f"api/v1/environment/?namespace={namespace}", method="GET"
            )
        return self._make_request("api/v1/environment/", method="GET")

    def delete_namespace(self, namespace: str) -> requests.Response:
        """Delete a namespace."""
        return self._make_request(f"api/v1/namespace/{namespace}", method="DELETE")

    @staticmethod
    def gen_random_namespace() -> str:
        """Generate a random namespace."""
        return uuid.uuid4().hex

    def set_active_build(
        self, namespace: str, environment: str, build_id: int
    ) -> requests.Response:
        """Set the active build for a given environment.

        Parameters
        ----------
        namespace : str
            Name of the namespace in which the environment lives
        environment : str
            Environment to set the build for
        build_id : int
            ID of the build to be activated for the given environment

        Returns
        -------
        requests.Response
            Response from the conda-store server.
        """
        return self._make_request(
            f"api/v1/environment/{namespace}/{environment}",
            method="PUT",
            json_data={"build_id": build_id},
        )

    def get_builds(
        self,
        environment: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get information about an environment.

        Parameters
        ----------
        namespace : Optional[str]
            Name of a namespace
        environment : Optional[str]
            Name of an environment

        Returns
        -------
        dict[str, Any]
            Dict of build properties; see API docs for
            api/v1/build/ for more information.
        """
        query_params = []
        if environment:
            query_params.append(f"name={environment}")

        if namespace:
            query_params.append(f"namespace={namespace}")

        return self._make_request(f'api/v1/build/?{"&".join(query_params)}').json()[
            "data"
        ]

    def get_environment(self, namespace: str, environment: str) -> dict[str, Any]:
        """Get information about an environment.

        Parameters
        ----------
        namespace : str
            Name of the namespace in which the environment lives
        environment : str
            Name of the environment

        Returns
        -------
        dict[str, Any]
            Dict of environment properties; see API docs for
            api/v1/environment/{namespace}/{environment}/ for more information.
        """
        return self._make_request(
            f"api/v1/environment/{namespace}/{environment}/"
        ).json()["data"]

    def cancel_build(self, build_id: int) -> requests.Response:
        """Cancel a build in progress.

        Parameters
        ----------
        build_id : int
            ID of the build to cancel

        Returns
        -------
        requests.Response
            Response from the server
        """
        return self._make_request(f"api/v1/build/{build_id}/cancel/", method="PUT")

    def get_build_status(self, build_id: int) -> BuildStatus:
        """Get the status of a build as a BuildStatus instance.

        Parameters
        ----------
        build_id : int
            ID of the build to get the status for

        Returns
        -------
        BuildStatus
            Build status for the given build ID
        """
        response = self._make_request(f"api/v1/build/{build_id}/")
        return BuildStatus(response.json()["data"]["status"])

    def get_lockfile(self, build_id: int) -> Dict[str, Any]:
        """Get a lockfile for the given build ID.
            Build for which the lockfile is to be retrieved

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the lockfile version, metadata, and packages
        """
        return json.loads(self._make_request(f"api/v1/build/{build_id}/lockfile").text)


def wait_for_condition(
    condition: Callable[[], bool], timeout: int = 60, interval: int = 1
):
    """Call `condition` until it returns `True`.

    `condition` will be called every `interval` seconds up to a maximum of `timeout`
    seconds, at which point a ValueError is raised.

    Parameters
    ----------
    condition : Callable[[], bool]
        Function to call until True is returned
    timeout : int
        Number of seconds to continue calling `condition` for before timing out
    interval : int
        Number of seconds between consecutive calls
    """
    initial_time = time.time()
    while time.time() - initial_time < timeout:
        result = condition()
        if result:
            return

        time.sleep(interval)

    raise ValueError(
        f"Timeout after {timeout}s waiting for condition. Last result: {result}"
    )
