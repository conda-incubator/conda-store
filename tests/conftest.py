import pytest

from conda_store.orm import new_session_factory
from conda_store.app import CondaStore


@pytest.fixture
def db():
    Session = new_session_factory(url='sqlite:///:memory:')
    yield Session()


@pytest.fixture(scope='module')
def conda_store():
    yield CondaStore(
        store_directory='/tmp/conda-store',
        database_url='sqlite:///:memory:',
        storage_backend='filesystem')
