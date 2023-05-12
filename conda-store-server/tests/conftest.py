import os
import pathlib
import datetime

import pytest
import yaml
from fastapi.testclient import TestClient

from conda_store_server import app, schema, dbutil, utils, testing, api
from conda_store_server.server import app as server_app


@pytest.fixture
def celery_config(conda_store):
    config = conda_store.celery_config
    config["traitlets"] = {"CondaStore": {"database_url": conda_store.database_url}}
    return config


@pytest.fixture
def conda_store_config(tmp_path):
    from traitlets.config import Config

    filename = pathlib.Path(tmp_path) / "database.sqlite"

    with utils.chdir(tmp_path):
        yield Config(CondaStore=dict(database_url=f"sqlite:///{filename}"))


@pytest.fixture
def conda_store_server(conda_store_config):
    _conda_store_server = server_app.CondaStoreServer(config=conda_store_config)
    _conda_store_server.initialize()
    _conda_store = _conda_store_server.conda_store
    _conda_store.ensure_settings()

    pathlib.Path(_conda_store.store_directory).mkdir(exist_ok=True)

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

    yield _conda_store_server


@pytest.fixture
def testclient(conda_store_server):
    return TestClient(conda_store_server.init_fastapi_app())


@pytest.fixture
def authenticate(testclient):
    response = testclient.post(
        "/login/", json={"username": "username", "password": "password"}
    )
    assert response.status_code == 200


@pytest.fixture
def seed_conda_store(conda_store):
    testing.seed_conda_store(
        conda_store,
        {
            "default": {
                "name1": schema.CondaSpecification(
                    name="name1",
                    channels=["conda-forge"],
                    dependencies=["numpy"],
                ),
                "name2": schema.CondaSpecification(
                    name="name2",
                    channels=["defaults"],
                    dependencies=["flask"],
                ),
            },
            "namespace1": {
                "name3": schema.CondaSpecification(
                    name="name3",
                    channels=["bioconda"],
                    dependencies=["numba"],
                )
            },
            "namespace2": {
                "name4": schema.CondaSpecification(
                    name="name4",
                    channels=["bioconda"],
                    dependencies=["numba"],
                )
            },
        },
    )

    # for testing purposes make build 4 complete
    build = api.get_build(conda_store.db, build_id=4)
    build.started_on = datetime.datetime.utcnow()
    build.ended_on = datetime.datetime.utcnow()
    build.status = schema.BuildStatus.COMPLETED
    conda_store.db.commit()


@pytest.fixture
def conda_store(conda_store_config):
    _conda_store = app.CondaStore(config=conda_store_config)
    _conda_store.ensure_settings()

    pathlib.Path(_conda_store.store_directory).mkdir(exist_ok=True)

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
