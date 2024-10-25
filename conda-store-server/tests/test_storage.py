import datetime

import pytest

from conda_store_server import storage
from conda_store_server._internal import schema
from conda_store_server import api


def test_fset_new_package(db):
    store = storage.Storage()
    store.fset(db, 123, "new_build_key", "", schema.BuildArtifactType.YAML)
    assert len(api.list_build_artifacts(db).all()) == 1


def test_fset_existing_package(seed_conda_store):
    store = storage.Storage()
    db = seed_conda_store
    
    inital_artifacts = api.list_build_artifacts(db).all()
    artifact = inital_artifacts[0]
    
    store.fset(db, artifact.build_id, artifact.key, "", artifact.artifact_type)
    assert len(api.list_build_artifacts(db).all()) == len(inital_artifacts)

def test_delete_existing_artifact(seed_conda_store):
    store = storage.Storage()
    db = seed_conda_store
    
    inital_artifacts = api.list_build_artifacts(db).all()
    artifact = inital_artifacts[0]
    
    store.delete(db, artifact.build_id, artifact.key)
    assert len(api.list_build_artifacts(db).all()) == len(inital_artifacts)-1
