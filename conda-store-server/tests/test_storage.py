import os

import pytest

from conda_store_server import api, storage
from conda_store_server._internal import schema


@pytest.fixture
def local_file_store(tmp_path):
    """Setup a tmp dir with 2 test files and a logs dir"""
    tf_one = str(tmp_path / "testfile1")
    with open(tf_one, "w") as file:
        file.write("testfile1")

    tf_two = str(tmp_path / "testfile2")
    with open(tf_two, "w") as file:
        file.write("testfile2")

    logs_path = tmp_path / "logs"
    os.mkdir(logs_path)

    return tmp_path


class TestStorage:
    def test_fset_new_package(self, db):
        store = storage.Storage()
        store.fset(db, 123, "new_build_key", "", schema.BuildArtifactType.YAML)
        assert len(api.list_build_artifacts(db).all()) == 1

    def test_fset_existing_package(self, seed_conda_store):
        store = storage.Storage()
        db = seed_conda_store

        inital_artifacts = api.list_build_artifacts(db).all()
        artifact = inital_artifacts[0]

        store.fset(db, artifact.build_id, artifact.key, "", artifact.artifact_type)
        assert len(api.list_build_artifacts(db).all()) == len(inital_artifacts)

    def test_delete_existing_artifact(self, seed_conda_store):
        store = storage.Storage()
        db = seed_conda_store

        inital_artifacts = api.list_build_artifacts(db).all()
        artifact = inital_artifacts[0]

        store.delete(db, artifact.build_id, artifact.key)
        assert len(api.list_build_artifacts(db).all()) == len(inital_artifacts) - 1


class TestLocalStorage:
    def test_fset_new_package(self, db, local_file_store):
        store = storage.LocalStorage()
        store.storage_path = local_file_store

        filename = str(local_file_store / "testfile1")
        store.fset(
            db,
            123,
            "new_build_key",
            filename,
            "contenttype",
            schema.BuildArtifactType.YAML,
        )
        assert len(api.list_build_artifacts(db).all()) == 1

        target_file = str(local_file_store / "new_build_key")
        assert os.path.exists(target_file)
        target_content = open(target_file).read()
        assert target_content == "testfile1"

    def test_fset_dont_overwrite_file(self, db, local_file_store):
        store = storage.LocalStorage()
        store.storage_path = local_file_store

        filename = str(local_file_store / "testfile1")
        store.fset(
            db, 123, "testfile2", filename, "contenttype", schema.BuildArtifactType.YAML
        )
        assert len(api.list_build_artifacts(db).all()) == 1

        target_file = str(local_file_store / "testfile2")
        assert os.path.exists(target_file)
        target_content = open(target_file).read()
        assert target_content == "testfile1"

    def test_set_new_package(self, db, local_file_store):
        store = storage.LocalStorage()
        store.storage_path = local_file_store

        store.set(
            db,
            123,
            "new_build_key",
            b"somestuff",
            "contenttype",
            schema.BuildArtifactType.YAML,
        )
        assert len(api.list_build_artifacts(db).all()) == 1

        target_file = str(local_file_store / "new_build_key")
        assert os.path.exists(target_file)
        target_content = open(target_file).read()
        assert target_content == "somestuff"

    def test_get(self, local_file_store):
        store = storage.LocalStorage()
        store.storage_path = local_file_store

        content = store.get("testfile1")
        assert content == b"testfile1"

    def test_delete(self, seed_conda_store, local_file_store):
        store = storage.LocalStorage()
        store.storage_path = local_file_store
        db = seed_conda_store

        inital_artifacts = api.list_build_artifacts(db).all()
        artifact = inital_artifacts[0]
        target_file = str(local_file_store / artifact.key)

        with open(target_file, "w") as file:
            file.write("testfile2")

        store.delete(db, artifact.build_id, artifact.key)
        assert len(api.list_build_artifacts(db).all()) == len(inital_artifacts) - 1

        assert not os.path.exists(target_file)
