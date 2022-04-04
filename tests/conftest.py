import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'conda-store-server'))

import pytest
from requests import Session
from urllib.parse import urljoin


CONDA_STORE_BASE_URL = os.environ.get('CONDA_STORE_BASE_URL', "http://localhost:5000/conda-store/")
CONDA_STORE_USERNAME = os.environ.get('CONDA_STORE_USERNAME', "username")
CONDA_STORE_PASSWORD = os.environ.get('CONDA_STORE_PASSWORD', "password")


class CondaStoreSession(Session):
    def __init__(self, prefix_url: str):
        self.prefix_url = prefix_url
        super().__init__()

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.prefix_url, url)
        return super().request(method, url, *args, **kwargs)

    def login(self, username: str = CONDA_STORE_USERNAME, password: str = CONDA_STORE_PASSWORD):
        response = super().post("login", json={
            "username": username,
            "password": password,
        })
        response.raise_for_status()


@pytest.fixture
def testclient():
    session = CondaStoreSession(CONDA_STORE_BASE_URL)
    yield session
