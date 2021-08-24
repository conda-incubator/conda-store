import shutil
import os

from celery.decorators import task
import yaml

from conda_store_server.worker.utils import create_worker
from conda_store_server import api, environment, utils, orm
from conda_store_server.build import (
    build_conda_environment,
    build_conda_env_export,
    build_conda_pack,
    build_conda_docker,
)


@task(name="task_watch_paths")
def task_watch_paths():
    worker = create_worker()

    environment_paths = environment.discover_environments(worker.watch_paths)
    for path in environment_paths:
        with open(path) as f:
            worker.conda_store.register_environment(
                specification=yaml.safe_load(f), namespace="filesystem"
            )

    worker.conda_store.session_factory.remove()


@task(name="task_update_storage_metrics")
def task_update_storage_metrics():
    conda_store = create_worker().conda_store
    conda_store.configuration.update_storage_metrics(
        conda_store.db, conda_store.store_directory
    )

    conda_store.session_factory.remove()


@task(name="task_update_conda_channels")
def task_update_conda_channels():
    conda_store = create_worker().conda_store

    conda_store.ensure_conda_channels()

    for channel in api.list_conda_channels(conda_store.db):
        channel.update_packages(conda_store.db)

    conda_store.session_factory.remove()


@task(name="task_build_conda_environment")
def task_build_conda_environment(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_environment(conda_store, build)
    conda_store.session_factory.remove()


@task(name="task_build_conda_env_export")
def task_build_conda_env_export(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_env_export(conda_store, build)
    conda_store.session_factory.remove()


@task(name="task_build_conda_pack")
def task_build_conda_pack(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_pack(conda_store, build)
    conda_store.session_factory.remove()


@task(name="task_build_conda_docker")
def task_build_conda_docker(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_docker(conda_store, build)
    conda_store.session_factory.remove()


@task(name="task_update_environment_build")
def task_update_environment_build(environment_id):
    conda_store = create_worker().conda_store
    environment = api.get_environment(conda_store.db, id=environment_id)

    conda_prefix = environment.build.build_path(conda_store.store_directory)
    environment_prefix = environment.build.environment_path(
        conda_store.environment_directory
    )

    utils.symlink(conda_prefix, environment_prefix)
    conda_store.session_factory.remove()


@task(name="task_delete_build")
def task_delete_build(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)

    conda_store.log.error("deleting artifacts")
    for build_artifact in api.list_build_artifacts(
        conda_store.db,
        limit=None,
        build_id=build_id,
        excluded_artifact_types=conda_store.build_artifacts_kept_on_deletion,
    ):
        if build_artifact.artifact_type == orm.BuildArtifactType.DIRECTORY:
            # ignore key
            conda_prefix = build.build_path(conda_store.store_directory)
            # be REALLY sure this is a directory within store directory
            if conda_prefix.startswith(conda_store.store_directory) and os.path.isdir(
                conda_prefix
            ):
                shutil.rmtree(conda_prefix)
                conda_store.db.delete(build_artifact)
        elif build_artifact.artifact_type == orm.BuildArtifactType.LOCKFILE:
            pass
        else:
            conda_store.log.error(f"deleting {build_artifact.key}")
            conda_store.storage.delete(conda_store.db, build_id, build_artifact.key)

    conda_store.db.commit()
    conda_store.session_factory.remove()
