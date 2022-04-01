import os

import pytest
from requests import Session
from urllib.parse import urljoin


CONDA_STORE_BASE_URL = os.environ.get('CONDA_STORE_BASE_URL', "http://localhost:5000/conda-store/")


class CondaStoreSession(Session):
    def __init__(self, prefix_url):
        self.prefix_url = prefix_url
        super().__init__()

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.prefix_url, url)
        print(url)
        return super().request(method, url, *args, **kwargs)


@pytest.fixture
def testclient():
    session = CondaStoreSession(CONDA_STORE_BASE_URL)
    yield session
