from celery.decorators import task
import yaml

from conda_store_server.worker.utils import create_worker
from conda_store_server import api, environment
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


@task(name="task_update_storage_metrics")
def task_update_storage_metrics():
    conda_store = create_worker().conda_store
    conda_store.configuration.update_storage_metrics(
        conda_store.db, conda_store.store_directory
    )


@task(name="task_update_conda_channels")
def task_update_conda_channels():
    conda_store = create_worker().conda_store

    conda_store.ensure_conda_channels()

    for channel in api.list_conda_channels(conda_store.db):
        channel.update_packages(conda_store.db)


@task(name="task_build_conda_environment")
def task_build_conda_environment(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_environment(conda_store, build)


@task(name="task_build_conda_env_export")
def task_build_conda_env_export(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_env_export(conda_store, build)


@task(name="task_build_conda_pack")
def task_build_conda_pack(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_pack(conda_store, build)


@task(name="task_build_conda_docker")
def task_build_conda_docker(build_id):
    conda_store = create_worker().conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_docker(conda_store, build)
