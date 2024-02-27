import datetime
import pathlib
import sys

import pytest
import yaml
from fastapi.testclient import TestClient

from conda_store_server import (  # isort:skip
    action,
    api,
    app,
    dbutil,
    schema,
    storage,
    testing,
    utils,
)

from conda_store_server.server import app as server_app  # isort:skip


@pytest.fixture
def celery_config(tmp_path, conda_store):
    config = conda_store.celery_config
    config["traitlets"] = {
        "CondaStore": {
            "database_url": conda_store.database_url,
            "store_directory": conda_store.store_directory,
        }
    }
    config["beat_schedule_filename"] = str(
        tmp_path / ".conda-store" / "celerybeat-schedule"
    )
    return config


@pytest.fixture
def conda_store_config(tmp_path, request):
    from traitlets.config import Config

    filename = tmp_path / ".conda-store" / "database.sqlite"

    store_directory = tmp_path / ".conda-store" / "state"
    store_directory.mkdir(parents=True)

    storage.LocalStorage.storage_path = str(tmp_path / ".conda-store" / "storage")

    with utils.chdir(tmp_path):
        yield Config(
            CondaStore=dict(
                storage_class=storage.LocalStorage,
                store_directory=str(store_directory),
                database_url=f"sqlite:///{filename}?check_same_thread=False",
            )
        )

    original_sys_argv = list(sys.argv)
    sys.argv = [sys.argv[0]]

    def teardown():
        sys.argv = list(original_sys_argv)

    request.addfinalizer(teardown)


@pytest.fixture
def conda_store_server(conda_store_config):
    _conda_store_server = server_app.CondaStoreServer(config=conda_store_config)
    _conda_store_server.initialize()

    _conda_store = _conda_store_server.conda_store

    pathlib.Path(_conda_store.store_directory).mkdir(exist_ok=True)

    dbutil.upgrade(_conda_store.database_url)

    with _conda_store.session_factory() as db:
        _conda_store.ensure_settings(db)
        _conda_store.configuration(db).update_storage_metrics(
            db, _conda_store.store_directory
        )

        _conda_store.celery_app

        # must import tasks after a celery app has been initialized
        import conda_store_server.worker.tasks  # noqa

        # ensure that models are created
        from celery.backends.database.session import ResultModelBase

        ResultModelBase.metadata.create_all(db.get_bind())

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
def seed_conda_store(db, conda_store):
    testing.seed_conda_store(
        db,
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
    build = api.get_build(db, build_id=4)
    build.started_on = datetime.datetime.utcnow()
    build.ended_on = datetime.datetime.utcnow()
    build.status = schema.BuildStatus.COMPLETED
    db.commit()


@pytest.fixture
def conda_store(conda_store_config):
    _conda_store = app.CondaStore(config=conda_store_config)

    pathlib.Path(_conda_store.store_directory).mkdir(exist_ok=True)

    dbutil.upgrade(_conda_store.database_url)

    with _conda_store.session_factory() as db:
        _conda_store.ensure_settings(db)
        _conda_store.configuration(db).update_storage_metrics(
            db, _conda_store.store_directory
        )

        _conda_store.celery_app

        # must import tasks after a celery app has been initialized
        import conda_store_server.worker.tasks  # noqa

        # ensure that models are created
        from celery.backends.database.session import ResultModelBase

        ResultModelBase.metadata.create_all(db.get_bind())

    yield _conda_store


@pytest.fixture
def db(conda_store):
    with conda_store.session_factory() as _db:
        yield _db


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


@pytest.fixture(
    params=[
        dict(
            name="test-prefix",
            channels=["main"],
            dependencies=["yaml"],
        ),
        dict(
            name="test-prefix",
            channels=["main"],
            dependencies=["python", {"pip": ["flask"]}],
        ),
    ]
)
def conda_prefix(conda_store, tmp_path, request):
    conda_prefix = tmp_path / "test-prefix"
    conda_prefix.mkdir()

    specification = schema.CondaSpecification(**request.param)

    action.action_install_specification(
        conda_command=conda_store.conda_command,
        specification=specification,
        conda_prefix=conda_prefix,
    )
    yield conda_prefix
