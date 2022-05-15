import shutil
import os
import random

from celery import Task, current_app
from celery.signals import worker_ready
import yaml
from sqlalchemy.exc import IntegrityError

from conda_store_server.worker.app import CondaStoreWorker
from conda_store_server import api, environment, utils, schema
from conda_store_server.build import (
    build_conda_environment,
    build_conda_env_export,
    build_conda_pack,
    build_conda_docker,
    solve_conda_environment,
)


@worker_ready.connect
def at_start(sender, **k):
    with sender.app.connection():
        sender.app.send_task("task_update_conda_channels")
        sender.app.send_task("task_update_storage_metrics")
        sender.app.send_task("task_watch_paths")


class WorkerTask(Task):
    _worker = None

    def after_return(self, *args, **kwargs):
        if self._worker is not None:
            self._worker.conda_store.session_factory.remove()

    @property
    def worker(self):
        if self._worker is None:
            self._worker = CondaStoreWorker()
            self._worker.initialize()
        return self._worker


@current_app.task(base=WorkerTask, name="task_watch_paths", bind=True)
def task_watch_paths(self):
    conda_store = self.worker.conda_store

    environment_paths = environment.discover_environments(self.worker.watch_paths)
    for path in environment_paths:
        with open(path) as f:
            conda_store.register_environment(
                specification=yaml.safe_load(f),
                namespace=conda_store.filesystem_namespace,
            )


@current_app.task(base=WorkerTask, name="task_update_storage_metrics", bind=True)
def task_update_storage_metrics(self):
    conda_store = self.worker.conda_store
    conda_store.configuration.update_storage_metrics(
        conda_store.db, conda_store.store_directory
    )


@current_app.task(base=WorkerTask, name="task_update_conda_channels", bind=True)
def task_update_conda_channels(self):
    conda_store = self.worker.conda_store
    try:
        conda_store.ensure_conda_channels()

        for channel in api.list_conda_channels(conda_store.db):
            channel.update_packages(conda_store.db, subdirs=conda_store.conda_platforms)
    except IntegrityError as exc:
        # there is a persistent error on startup that when the conda
        # channels are out of data and two tasks try to add the same
        # packages it runs into integrity errors the solution is to
        # let one of them finish and the other try again at a later
        # time
        self.retry(exc=exc, countdown=random.randrange(15, 30))


@current_app.task(base=WorkerTask, name="task_solve_conda_environment", bind=True)
def task_solve_conda_environment(self, solve_id):
    conda_store = self.worker.conda_store
    solve = api.get_solve(conda_store.db, solve_id)
    solve_conda_environment(conda_store, solve)


@current_app.task(base=WorkerTask, name="task_build_conda_environment", bind=True)
def task_build_conda_environment(self, build_id):
    conda_store = self.worker.conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_environment(conda_store, build)


@current_app.task(base=WorkerTask, name="task_build_conda_env_export", bind=True)
def task_build_conda_env_export(self, build_id):
    conda_store = self.worker.conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_env_export(conda_store, build)


@current_app.task(base=WorkerTask, name="task_build_conda_pack", bind=True)
def task_build_conda_pack(self, build_id):
    conda_store = self.worker.conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_pack(conda_store, build)


@current_app.task(base=WorkerTask, name="task_build_conda_docker", bind=True)
def task_build_conda_docker(self, build_id):
    conda_store = self.worker.conda_store
    build = api.get_build(conda_store.db, build_id)
    build_conda_docker(conda_store, build)


@current_app.task(base=WorkerTask, name="task_update_environment_build", bind=True)
def task_update_environment_build(self, environment_id):
    conda_store = self.worker.conda_store
    environment = api.get_environment(conda_store.db, id=environment_id)

    conda_prefix = environment.current_build.build_path(conda_store)
    environment_prefix = environment.current_build.environment_path(conda_store)

    utils.symlink(conda_prefix, environment_prefix)


def delete_build_artifact(conda_store, build_artifact):
    if build_artifact.artifact_type == schema.BuildArtifactType.DIRECTORY:
        # ignore key
        conda_prefix = build_artifact.build.build_path(conda_store)
        # be REALLY sure this is a directory within store directory
        if conda_prefix.startswith(conda_store.store_directory) and os.path.isdir(
            conda_prefix
        ):
            shutil.rmtree(conda_prefix)
            conda_store.db.delete(build_artifact)
    elif build_artifact.artifact_type == schema.BuildArtifactType.LOCKFILE:
        pass
    else:
        conda_store.log.info(f"deleting {build_artifact.key}")
        conda_store.storage.delete(
            conda_store.db, build_artifact.build.id, build_artifact.key
        )


@current_app.task(base=WorkerTask, name="task_delete_build", bind=True)
def task_delete_build(self, build_id):
    conda_store = self.worker.conda_store
    build = api.get_build(conda_store.db, build_id)

    conda_store.log.info(f"deleting artifacts for build={build.id}")
    for build_artifact in api.list_build_artifacts(
        conda_store.db,
        build_id=build_id,
        excluded_artifact_types=conda_store.build_artifacts_kept_on_deletion,
    ).all():
        delete_build_artifact(conda_store, build_artifact)
    conda_store.db.commit()


@current_app.task(base=WorkerTask, name="task_delete_environment", bind=True)
def task_delete_environment(self, environment_id):
    conda_store = self.worker.conda_store
    environment = api.get_environment(conda_store.db, id=environment_id)

    for build in environment.builds:
        conda_store.log.info(f"deleting artifacts for build={build.id}")
        for build_artifact in api.list_build_artifacts(
            conda_store.db,
            build_id=build.id,
        ).all():
            delete_build_artifact(conda_store, build_artifact)

    conda_store.db.delete(environment)
    conda_store.db.commit()


@current_app.task(base=WorkerTask, name="task_delete_namespace", bind=True)
def task_delete_namespace(self, namespace_id):
    conda_store = self.worker.conda_store
    namespace = api.get_namespace(conda_store.db, id=namespace_id)

    for environment_orm in namespace.environments:
        for build in environment_orm.builds:
            conda_store.log.info(f"deleting artifacts for build={build.id}")
            for build_artifact in api.list_build_artifacts(
                conda_store.db,
                build_id=build.id,
            ).all():
                delete_build_artifact(conda_store, build_artifact)
        conda_store.db.delete(environment_orm)
    conda_store.db.delete(namespace)
    conda_store.db.commit()
