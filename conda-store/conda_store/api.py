import datetime
import math
import os
from typing import Dict, List

import yarl
from conda_store import auth, exception, utils


class CondaStoreAPIError(exception.CondaStoreError):
    pass


class CondaStoreAPI:
    def __init__(
        self, conda_store_url: str, auth_type: str = "none", verify_ssl=True, **kwargs
    ):
        self.conda_store_url = yarl.URL(conda_store_url)
        self.api_url = self.conda_store_url / "api/v1"
        self.auth_type = auth_type
        self.verify_ssl = verify_ssl

        if auth_type == "token":
            self.api_token = kwargs.get("api_token", os.environ["CONDA_STORE_TOKEN"])
        elif auth_type == "basic":
            self.username = kwargs.get("username", os.environ["CONDA_STORE_USERNAME"])
            self.password = kwargs.get("password", os.environ["CONDA_STORE_PASSWORD"])

    async def __aenter__(self):
        if self.auth_type == "none":
            self.session = await auth.none_authentication(verify_ssl=self.verify_ssl)
        elif self.auth_type == "token":
            self.session = await auth.token_authentication(
                self.api_token, verify_ssl=self.verify_ssl
            )
        elif self.auth_type == "basic":
            self.session = await auth.basic_authentication(
                self.conda_store_url,
                self.username,
                self.password,
                verify_ssl=self.verify_ssl,
            )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def get_paginated_request(self, url: yarl.URL, max_pages=None, **kwargs):
        data = []

        async with self.session.get(utils.ensure_slash(url)) as response:
            response_data = await response.json()
            num_pages = math.ceil(response_data["count"] / response_data["size"])
            data.extend(response_data["data"])

        if max_pages is not None:
            num_pages = min(max_pages, num_pages)

        for page in range(2, num_pages + 1):
            async with self.session.get(
                utils.ensure_slash(url % {"page": page})
            ) as response:
                data.extend((await response.json())["data"])

        return data

    async def get_permissions(self):
        async with self.session.get(
            utils.ensure_slash(self.api_url / "permission")
        ) as response:
            return (await response.json())["data"]

    async def create_token(
        self,
        primary_namespace: str = None,
        role_bindings: Dict[str, List[str]] = None,
        expiration: datetime.datetime = None,
    ):
        current_permissions = await self.get_permissions()
        requested_permissions = {
            "primary_namespace": primary_namespace
            or current_permissions["primary_namespace"],
            "role_bindings": role_bindings or current_permissions["entity_roles"],
            "exp": expiration or current_permissions["expiration"],
        }
        async with self.session.post(
            utils.ensure_slash(self.api_url / "token"), json=requested_permissions
        ) as response:
            if response.status == 400:
                raise CondaStoreAPIError((await response.json())["message"])

            return (await response.json())["data"]["token"]

    async def list_namespaces(self):
        return await self.get_paginated_request(self.api_url / "namespace" / "")

    async def create_namespace(self, namespace: str):
        async with self.session.post(
            utils.ensure_slash(self.api_url / "namespace" / namespace)
        ) as response:
            if response.status != 200:
                raise CondaStoreAPIError(f"Error creating namespace {namespace}")

    async def delete_namespace(self, namespace: str):
        async with self.session.delete(
            utils.ensure_slash(self.api_url / "namespace" / namespace)
        ) as response:
            if response.status != 200:
                raise CondaStoreAPIError(f"Error deleting namespace {namespace}")

    async def list_environments(self, status: str, artifact: str, packages: List[str]):
        url = self.api_url / "environment"
        if status:
            url = url % {"status": status}
        if artifact:
            url = url % {"artifact": artifact}
        if packages:
            url = url % {"packages": packages}
        return await self.get_paginated_request(url)

    async def delete_environment(self, namespace: str, name: str):
        async with self.session.delete(
            utils.ensure_slash(self.api_url / "environment" / namespace / name)
        ) as response:
            if response.status != 200:
                raise CondaStoreAPIError(
                    f"Error deleting environment {namespace}/{name}"
                )

    async def create_environment(self, namespace: str, specification: str):
        async with self.session.post(
            utils.ensure_slash(self.api_url / "specification"),
            json={
                "namespace": namespace,
                "specification": specification,
            },
        ) as response:
            data = await response.json()
            if response.status != 200:
                message = data["message"]
                raise CondaStoreAPIError(
                    f"Error creating environment in namespace {namespace}\nReason {message}"
                )

            return data["data"]["build_id"]

    async def get_environment(self, namespace: str, name: str):
        async with self.session.get(
            utils.ensure_slash(self.api_url / "environment" / namespace / name)
        ) as response:
            if response.status != 200:
                raise CondaStoreAPIError(
                    f"Error getting environment {namespace}/{name}"
                )

            return (await response.json())["data"]

    async def solve_environment(
        self, channels: List[str], conda: List[str], pip: List[str]
    ):
        async with self.session.get(
            utils.ensure_slash(
                self.api_url
                / "specification"
                % {
                    "channels": channels,
                    "conda": conda,
                    "pip": pip,
                }
            )
        ) as response:
            return (await response.json())["solve"]

    async def list_builds(self, status: str, artifact: str, packages: List[str]):
        url = self.api_url / "build"
        if status:
            url = url % {"status": status}
        if artifact:
            url = url % {"artifact": artifact}
        if packages:
            url = url % {"packages": packages}
        return await self.get_paginated_request(url)

    async def get_build(self, build_id: int):
        async with self.session.get(
            utils.ensure_slash(self.api_url / "build" / str(build_id))
        ) as response:
            if response.status != 200:
                raise CondaStoreAPIError(f"Error getting build {build_id}")

            return (await response.json())["data"]

    async def download(self, build_id: int, artifact: str) -> bytes:
        url = self.api_url / "build" / str(build_id) / artifact / ""
        async with self.session.get(utils.ensure_slash(url)) as response:
            if response.status != 200:
                raise CondaStoreAPIError(f"Error downloading build {build_id}")

            return await response.content.read()
