import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'conda-store-server'))

import pytest
from conda_store_server import orm, schema


@pytest.fixture(scope="function")
def sqlalchemy_declarative_base():
    return orm.Base


@pytest.fixture(scope="function")
def sqlalchemy_mock_config():
    return [("build", [
        {
            "id": 1,
            "specification_id": 1,
            "environment_id": 1,
            "status": schema.BuildStatus.COMPLETED,
        },
    ]),("build_artifact", [
        {
            "id": 1,
            "build_id": 1,
            "artifact_type": schema.BuildArtifactType.LOCKFILE
        }
    ]),("build_conda_package", [
        {
            "build_id": 1,
            "conda_package_build_id": 1,
        },
        {
            "build_id": 1,
            "conda_package_build_id": 2,
        },
    ]),("conda_package_build", [
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
    ]),("conda_package", [
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
    ]),("conda_channel", [
        {
            "id": 1,
            "name": "https://conda.anaconda.org/conda-forge"
        },
    ])
    ]