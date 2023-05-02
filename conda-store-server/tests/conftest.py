import os
import pathlib

import pytest
import yaml

from conda_store_server import app, schema, dbutil, utils


@pytest.fixture
def celery_config(conda_store):
    config = conda_store.celery_config
    config["traitlets"] = {"CondaStore": {"database_url": conda_store.database_url}}
    return config


@pytest.fixture
def conda_store(tmp_path):
    with utils.chdir(tmp_path):
        filename = pathlib.Path(tmp_path) / "database.sqlite"

        _conda_store = app.CondaStore()
        _conda_store.database_url = f"sqlite:///{filename}"
        pathlib.Path(_conda_store.store_directory).mkdir()

        dbutil.upgrade(_conda_store.database_url)

        _conda_store.celery_app

        # must import tasks after a celery app has been initialized
        import conda_store_server.worker.tasks  # noqa

        # ensure that models are created
        from celery.backends.database.session import ResultModelBase

        ResultModelBase.metadata.create_all(_conda_store.db.get_bind())

        _conda_store.configuration.update_storage_metrics(
            _conda_store.db, _conda_store.store_directory
        )

        yield _conda_store


@pytest.fixture
def simple_specification():
    yield schema.CondaSpecification(
        name="test",
        channels=["main"],
        dependencies=["zlib"],
    )


@pytest.fixture
def simple_specification_with_pip():
    yield schema.CondaSpecification(
        name="test",
        channels=["main"],
        dependencies=[
            "python",
            {"pip": ["flask"]},
        ],
    )


@pytest.fixture
def simple_conda_lock():
    with (pathlib.Path(__file__).parent / "assets/conda-lock.zlib.yaml").open() as f:
        return yaml.safe_load(f)


@pytest.fixture
def current_prefix():
    return pathlib.Path(os.environ["CONDA_PREFIX"])
