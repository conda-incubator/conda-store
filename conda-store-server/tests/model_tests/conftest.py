import os
import sys

sys.path.append(os.path.join(os.getcwd(), 'conda-store-server'))

import pytest  # noqa: E402
from conda_store_server import orm, schema  # noqa: E402
from sqlalchemy.orm import mapper, sessionmaker  # noqa: E402
from sqlalchemy import create_engine, insert  # noqa: E402
from typing import TYPE_CHECKING  # noqa: E402

if TYPE_CHECKING:
    from sqlalchemy.orm import Session  # noqa: E402


@pytest.fixture(scope="function")
def sqlalchemy_declarative_base():
    return orm.Base


@pytest.fixture(scope="function")
def sqlalchemy_model_fixtures():
    return [("build", [
        {
            "id": 1,
            "specification_id": 1,
            "environment_id": 1,
            "status": schema.BuildStatus.COMPLETED,
        },
    ]), ("build_artifact", [
        {
            "id": 1,
            "build_id": 1,
            "artifact_type": schema.BuildArtifactType.LOCKFILE
        }
    ]), ("build_conda_package", [
        {
            "build_id": 1,
            "conda_package_build_id": 1,
        },
        {
            "build_id": 1,
            "conda_package_build_id": 2,
        },
    ]), ("conda_package_build", [
        {
            "id": 1,
            "package_id": 1,
            "channel_id": 1,
            "subdir": "linux-64",
            "build": "h27087fc_0",
            "build_number": 1,
            "depends": "[]",
            "sha256": "sha256",
            "size": 2314454,
            "tarball_ext": ".conda",
            "md5": "87473a15119779e021c314249d4b4aed",
        },
        {
            "id": 2,
            "package_id": 2,
            "channel_id": 1,
            "subdir": "linux-64",
            "build": "pyhd8ed1ab_0",
            "build_number": 1,
            "depends": "[]",
            "sha256": "sha256",
            "size": 2314454,
            "tarball_ext": ".tar.bz2",
            "md5": "37d4251d34eb991ff9e40e546cc2e803",
        },
    ]), ("conda_package", [
        {
            "id": 1,
            "channel_id": 1,
            "name": "icu",
            "version": "70.1",
        },
        {
            "id": 2,
            "channel_id": 1,
            "name": "zarr",
            "version": "2.12.0",
        }
    ]), ("conda_channel", [
        {
            "id": 1,
            "name": "https://conda.anaconda.org/conda-forge"
        },
    ])
    ]


@pytest.fixture(scope="session")
def connection_url():
    return "sqlite:///:memory:"


@pytest.fixture(scope="function")
def engine(connection_url):
    return create_engine(connection_url)


@pytest.fixture(scope="function")
def connection(engine, sqlalchemy_declarative_base):
    if sqlalchemy_declarative_base:
        sqlalchemy_declarative_base.metadata.create_all(engine)
    return engine.connect()


@pytest.fixture(scope="function")
def session(connection):
    session: Session = sessionmaker()(bind=connection)
    yield session
    session.close()


@pytest.fixture(scope="function")
def db_session(
        connection, sqlalchemy_declarative_base, sqlalchemy_model_fixtures
):
    # cribbed from https://github.com/resulyrt93/pytest-sqlalchemy-mock
    # with added support for `conda_store_server.orm.build_conda_package` m2m
    session: Session = sessionmaker()(bind=connection)

    def get_model_class_with_table_name(table_name: str):
        for mapper in sqlalchemy_declarative_base.registry.mappers:
            cls = mapper.class_
            if cls.__tablename__ == table_name:
                return cls

    if sqlalchemy_declarative_base and sqlalchemy_model_fixtures:
        through_m2m_table, m2m_data = None, None
        for model_config in sqlalchemy_model_fixtures:
            table_name, data = model_config

            if table_name == "build_conda_package":
                through_m2m_table, m2m_data = orm.build_conda_package, data

            model_class = get_model_class_with_table_name(table_name)
            if model_class:
                for datum in data:
                    instance = model_class(**datum)
                    session.add(instance)

        session.commit()

        for datum in m2m_data:
            stmt = through_m2m_table.insert().values(**datum)
            connection.execute(stmt)

    yield session
    session.close()
