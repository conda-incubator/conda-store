# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import datetime
import json
import pathlib
import sys
import typing
import uuid

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conda_store_server import api, app, storage

from conda_store_server._internal import (  # isort:skip
    action,
    dbutil,
    utils,
    conda_utils,
    orm,
    schema,
)

from conda_store_server._internal.server import app as server_app  # isort:skip


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
def conda_store_config(tmp_path):
    """A conda store configuration fixture.

    sys.path is manipulated so that only the name of the called program
    (e.g. `pytest`) is present. This prevents traitlets from parsing any
    additional pytest args as configuration settings to be applied to
    the conda-store-server.
    """
    from traitlets.config import Config

    filename = tmp_path / ".conda-store" / "database.sqlite"

    store_directory = tmp_path / ".conda-store" / "state"
    store_directory.mkdir(parents=True)

    storage.LocalStorage.storage_path = str(tmp_path / ".conda-store" / "storage")

    original_sys_argv = list(sys.argv)
    sys.argv = [sys.argv[0]]

    with utils.chdir(tmp_path):
        yield Config(
            CondaStore=dict(
                storage_class=storage.LocalStorage,
                store_directory=str(store_directory),
                database_url=f"sqlite:///{filename}?check_same_thread=False",
            )
        )

    sys.argv = list(original_sys_argv)


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
        # ensure that models are created
        from celery.backends.database.session import ResultModelBase

        import conda_store_server._internal.worker.tasks  # noqa

        ResultModelBase.metadata.create_all(db.get_bind())

    return _conda_store_server


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
    _seed_conda_store(
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
    return db


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
        # ensure that models are created
        from celery.backends.database.session import ResultModelBase

        import conda_store_server._internal.worker.tasks  # noqa

        ResultModelBase.metadata.create_all(db.get_bind())

    return _conda_store


@pytest.fixture
def db(conda_store):
    with conda_store.session_factory() as _db:
        yield _db


@pytest.fixture
def simple_specification():
    return schema.CondaSpecification(
        name="test",
        channels=["main"],
        dependencies=["zlib"],
    )


@pytest.fixture
def simple_specification_with_pip():
    return schema.CondaSpecification(
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
def simple_conda_lock_with_pip():
    with (
        pathlib.Path(__file__).parent / "assets/conda-lock.zlib.flask.yaml"
    ).open() as f:
        return yaml.safe_load(f)


@pytest.fixture
def simple_lockfile_specification(simple_conda_lock):
    return schema.LockfileSpecification.parse_obj(
        {
            "name": "test",
            "description": "simple lockfile specification",
            "lockfile": simple_conda_lock,
        }
    )


@pytest.fixture
def simple_lockfile_specification_with_pip(simple_conda_lock_with_pip):
    return schema.LockfileSpecification.parse_obj(
        {
            "name": "test",
            "description": "simple lockfile specification with pip",
            "lockfile": simple_conda_lock_with_pip,
        }
    )


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
    return conda_prefix


def _seed_conda_store(
    db: Session,
    conda_store,
    config: typing.Dict[str, typing.Dict[str, schema.CondaSpecification]] = {},
):
    for namespace_name in config:
        namespace = api.ensure_namespace(db, name=namespace_name)
        for environment_name, specification in config[namespace_name].items():
            environment = api.ensure_environment(
                db,
                name=specification.name,
                namespace_id=namespace.id,
            )
            specification = api.ensure_specification(db, specification)
            build = api.create_build(db, environment.id, specification.id)
            db.commit()

            environment.current_build_id = build.id
            db.commit()

            _create_build_artifacts(db, conda_store, build)
            _create_build_packages(db, conda_store, build)

            api.create_solve(db, specification.id)
            db.commit()


def _create_build_packages(db: Session, conda_store, build: orm.Build):
    channel_name = conda_utils.normalize_channel_name(
        conda_store.conda_channel_alias, "conda-forge"
    )
    channel = api.ensure_conda_channel(db, channel_name)

    conda_package = orm.CondaPackage(
        name=f"madeup-{uuid.uuid4()}",
        version="1.2.3",
        channel_id=channel.id,
    )
    db.add(conda_package)
    db.commit()

    conda_package_build = orm.CondaPackageBuild(
        package_id=conda_package.id,
        build="fakebuild",
        build_number=1,
        constrains=[],
        depends=[],
        md5=str(uuid.uuid4()),
        sha256=str(uuid.uuid4()),
        size=123456,
        subdir="noarch",
        timestamp=12345667,
    )
    db.add(conda_package_build)
    db.commit()

    build.package_builds.append(conda_package_build)
    db.commit()


def _create_build_artifacts(db: Session, conda_store, build: orm.Build):
    conda_store.storage.set(
        db,
        build.id,
        build.log_key,
        b"fake logs",
        content_type="text/plain",
        artifact_type=schema.BuildArtifactType.LOGS,
    )

    directory_build_artifact = orm.BuildArtifact(
        build_id=build.id,
        artifact_type=schema.BuildArtifactType.DIRECTORY,
        key=str(build.build_path(conda_store)),
    )
    db.add(directory_build_artifact)

    lockfile_build_artifact = orm.BuildArtifact(
        build_id=build.id, artifact_type=schema.BuildArtifactType.LOCKFILE, key=""
    )
    db.add(lockfile_build_artifact)

    conda_store.storage.set(
        db,
        build.id,
        build.conda_env_export_key,
        json.dumps(
            dict(name="testing", channels=["conda-forge"], dependencies=["numpy"])
        ).encode("utf-8"),
        content_type="text/yaml",
        artifact_type=schema.BuildArtifactType.YAML,
    )

    conda_store.storage.set(
        db,
        build.id,
        build.conda_pack_key,
        b"testing-conda-package",
        content_type="application/gzip",
        artifact_type=schema.BuildArtifactType.CONDA_PACK,
    )

    # have not included docker at the moment
