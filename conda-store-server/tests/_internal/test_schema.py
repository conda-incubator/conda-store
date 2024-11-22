# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest

from conda_store_server._internal import schema


@pytest.fixture
def test_lockfile():
    return {
        "version": 1,
        "metadata": {
            "content_hash": {
                "linux-64": "5514f6769db31a2037c24116f89239737c66d009b2d0c71e2872339c3cf1a8f6"
            },
            "channels": [{"url": "conda-forge", "used_env_vars": []}],
            "platforms": ["linux-64"],
            "sources": ["environment.yaml"],
        },
        "package": [
            {
                "name": "_libgcc_mutex",
                "version": "0.1",
                "manager": "conda",
                "platform": "linux-64",
                "dependencies": {},
                "url": "https://conda.anaconda.org/conda-forge/linux-64/_libgcc_mutex-0.1-conda_forge.tar.bz2",
                "hash": {
                    "md5": "d7c89558ba9fa0495403155b64376d81",
                    "sha256": "fe51de6107f9edc7aa4f786a70f4a883943bc9d39b3bb7307c04c41410990726",
                },
                "category": "main",
                "optional": False,
            },
            {
                "name": "_openmp_mutex",
                "version": "4.5",
                "manager": "conda",
                "platform": "linux-64",
                "dependencies": {"_libgcc_mutex": "0.1", "libgomp": ">=7.5.0"},
                "url": "https://conda.anaconda.org/conda-forge/linux-64/_openmp_mutex-4.5-2_gnu.tar.bz2",
                "hash": {
                    "md5": "73aaf86a425cc6e73fcf236a5a46396d",
                    "sha256": "fbe2c5e56a653bebb982eda4876a9178aedfc2b545f25d0ce9c4c0b508253d22",
                },
                "category": "main",
                "optional": False,
            },
        ],
    }


def test_parse_lockfile_obj(test_lockfile):
    lockfile_spec = {
        "name": "test",
        "description": "test",
        # use a copy of the lockfile so it's not mutated and we can compare
        # against the original dict
        "lockfile": test_lockfile.copy(),
    }
    specification = schema.LockfileSpecification.parse_obj(lockfile_spec)
    assert specification.model_dump()["lockfile"] == test_lockfile
