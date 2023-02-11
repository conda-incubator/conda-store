import os
import sys

sys.path.append(os.path.join(os.getcwd(), 'conda-store-server'))

import pytest  # noqa: E402
from conda_store_server import orm, schema  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from typing import TYPE_CHECKING  # noqa: E402

if TYPE_CHECKING:
    from sqlalchemy.orm import Session  # noqa: E402


@pytest.fixture(scope="function")
def sqlalchemy_declarative_base():
    return orm.Base


@pytest.fixture(scope="function")
def sqlalchemy_model_fixtures():
    return {
        orm.Build: [
            {
                "id": 1,
                "specification_id": 1,
                "environment_id": 1,
                "status": schema.BuildStatus.COMPLETED,
            }
        ],
        orm.BuildArtifact: [
            {
                "id": 1,
                "build_id": 1,
                "artifact_type": schema.BuildArtifactType.LOCKFILE
            }
        ],
        orm.build_conda_package: [
            {
                "build_id": 1,
                "conda_package_build_id": 1,
            },
            {
                "build_id": 1,
                "conda_package_build_id": 2,
            }
        ],
        orm.CondaPackageBuild: [
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
            {
                "id": 3,
                "package_id": 1,
                "channel_id": 1,
                "subdir": "linux-64",
                "build": "h27087fc_0",
                "build_number": 1,
                "depends": "[]",
                "sha256": "thesha256",
                "size": 2314454,
                "tarball_ext": None,
                "md5": "97473a15119779e021c314249d4b4aed",
            }
        ],
        orm.CondaPackage: [
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
        ],
        orm.CondaChannel: [
            {
                "id": 1,
                "name": "https://conda.anaconda.org/conda-forge"
            }
        ]
    }


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

    if sqlalchemy_declarative_base and sqlalchemy_model_fixtures:

        through_m2m_tables_and_data = []
        for model_config in sqlalchemy_model_fixtures.items():
            model_class, data = model_config
            # handle things that inherit from `declarative_base`
            if hasattr(model_class, "mro"):
                for datum in data:
                    instance = model_class(**datum)
                    session.add(instance)
            else:
                through_m2m_tables_and_data.append((model_class, data))

        # shouldn't need to do this
        # but given that non-declarative-base models
        # cannot use `session.add` and only `connection.execute`
        # means we need to actually persist these things
        session.commit()

        # handle m2m(s)
        for m2m_model_class, m2m_data in through_m2m_tables_and_data:
            for datum in m2m_data:
                stmt = m2m_model_class.insert().values(**datum)
                connection.execute(stmt)

    yield session
    session.close()
