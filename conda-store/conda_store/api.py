import os
import math

import yarl
import aiohttp

from conda_store import auth, exception


class CondaStoreAPIError(exception.CondaStoreError):
    pass


class CondaStoreAPI:
    def __init__(self, conda_store_url: str, auth_type: str = "token", verify_ssl=True, **kwargs):
        self.conda_store_url = yarl.URL(conda_store_url)
        self.api_url = self.conda_store_url / "api/v1"
        self.auth_type = auth_type
        self.verify_ssl = verify_ssl

        if auth_type == "token":
            self.api_token = kwargs.get("api_token", os.environ["CONDA_STORE_TOKEN"])

    async def __aenter__(self):
        if self.auth_type == "token":
            token = os.environ.get('CONDA_STORE_TOKEN', self.api_token)
            self.session = await auth.token_authentication(
                self.api_token, verify_ssl=self.verify_ssl
            )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def get_paginated_request(self, url: yarl.URL, max_pages=None, **kwargs):
        data = []

        async with self.session.get(url) as response:
            response_data = await response.json()
            num_pages = math.ceil(response_data['count'] / response_data['size'])
            data.extend(response_data['data'])

        if max_pages is not None:
            num_pages = min(max_pages, num_pages)

        for page in range(2, num_pages+1):
            async with self.session.get(url % {"page": page}) as response:
                data.extend((await response.json())['data'])

        return data

    async def get_permissions(self):
        async with self.session.get(self.api_url / "permission") as response:
            return (await response.json())['data']

    async def list_namespaces(self):
        return await self.get_paginated_request(self.api_url / "namespace")

    async def create_namespace(self, namespace: str):
        async with self.session.post(self.api_url / "namespace" / namespace) as response:
            if response.status != 200:
                raise CondaStoreAPIError(f"Error creating namespace {namespace}")

    async def delete_namespace(self, namespace: str):
        async with self.session.delete(self.api_url / "namespace" / namespace) as response:
            if response.status != 200:
                raise CondaStoreAPIError(f"Error deleting namespace {namespace}")

    async def list_environments(self):
        return await self.get_paginated_request(self.api_url / "environment")

    async def delete_environment(self, namespace: str, name: str):
        async with self.session.delete(self.api_url / "environment" / namespace / name) as response:
            if response.status != 200:
                raise CondaStoreAPIError(f"Error deleting environment {namespace}/{name}")

    async def create_environment(self, namespace: str, specification: str):
        async with self.session.post(self.api_url / "specification", json={
                "namespace": namespace,
                "specification": specification,
        }) as response:
            data = await response.json()
            if response.status != 200:
                message = data['message']
                raise CondaStoreAPIError(f"Error creating environment in namespace {namespace}\nReason {message}")

            return data["data"]["build_id"]

    async def get_environment(self, namespace: str, name: str):
        async with self.session.get(self.api_url / "environment" / namespace / name) as response:
            if response.status != 200:
                raise CondaStoreAPIError(f"Error getting environment {namespace}/{name}")

            return (await response.json())['data']

    async def download(self, build_id: str, artifact: str):
        pass
