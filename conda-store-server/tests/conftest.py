import datetime
import os
import pathlib

import pytest
import yaml

from conda_store_server import app, schema, dbutil, utils


@pytest.fixture
def conda_store(tmp_path):
    with utils.chdir(tmp_path):
        filename = pathlib.Path(tmp_path) / "database.sqlite"

        _conda_store = app.CondaStore()
        _conda_store.database_url = f"sqlite:///{filename}"
        pathlib.Path(_conda_store.store_directory).mkdir()

        dbutil.upgrade(_conda_store.database_url)

        _conda_store.configuration.update_storage_metrics(
            _conda_store.db, _conda_store.store_directory
        )

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
    with (pathlib.Path(__file__).parent / "assets/conda-lock.zlib.yaml").open() as f:
        return yaml.safe_load(f)


@pytest.fixture
def current_prefix():
    return pathlib.Path(os.environ["CONDA_PREFIX"])
