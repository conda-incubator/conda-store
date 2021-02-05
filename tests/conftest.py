import pytest

from conda_store.orm import new_session_factory
from conda_store.app import CondaStore


@pytest.fixture
def db():
    Session = new_session_factory(url='sqlite:///:memory:')
    yield Session()


@pytest.fixture(scope='session')
def conda_store():
    yield CondaStore(store_directory='/tmp', database_url='sqlite:///:memory:')
