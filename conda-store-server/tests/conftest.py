import datetime
import os
import pathlib

import pytest
import yaml

from conda_store_server import app, schema


@pytest.fixture
def conda_store():
    _conda_store = app.CondaStore()
    _conda_store.database_url = "sqlite:///:memory:"
    yield _conda_store


@pytest.fixture
def simple_specification():
    yield schema.Specification(
        id=1,
        name="test",
        spec={
            "name": "test",
            "channels": ["conda-forge"],
            "dependencies": ["zlib"],
        },
        sha256="...",
        created_on=datetime.datetime.utcnow(),
    )


@pytest.fixture
def simple_specification_with_pip():
    yield schema.Specification(
        id=1,
        name="test",
        spec={
            "name": "test",
            "channels": ["conda-forge"],
            "dependencies": [
                "python",
                {"pip": ["flask"]},
            ],
        },
        sha256="...",
        created_on=datetime.datetime.utcnow(),
    )


@pytest.fixture
def simple_conda_lock():
    with open("tests/assets/conda-lock.zlib.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def current_prefix():
    return pathlib.Path(os.environ["CONDA_PREFIX"])
