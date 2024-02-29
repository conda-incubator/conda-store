import datetime
import os
import shutil
import sys
import typing

import yaml
from celery import Task, platforms, shared_task
from celery.execute import send_task
from celery.signals import worker_ready
from conda_store_server import api, environment, schema, utils
from conda_store_server.build import (
    build_cleanup,
    build_conda_docker,
    build_conda_env_export,
    build_conda_environment,
    build_conda_pack,
    build_constructor_installer,
    solve_conda_environment,
)
from conda_store_server.worker.app import CondaStoreWorker
from filelock import FileLock
from sqlalchemy.orm import Session


@worker_ready.connect
def at_start(sender, **k):
    with sender.app.connection():
        sender.app.send_task("task_initialize_worker")
        sender.app.send_task("task_update_conda_channels")
        sender.app.send_task("task_watch_paths")
        sender.app.send_task("task_cleanup_builds")


class WorkerTask(Task):
    @property
    def worker(self):
        if not hasattr(self, "_worker"):
            self._worker = CondaStoreWorker()

            # hook to allow for traitlet configuration via celery config
            if "traitlets" in self.app.conf:
                from traitlets.config.loader import Config

                config = Config(**self.app.conf.traitlets)
                self._worker.update_config(config)

            self._worker.initialize()

        # Installs a signal handler that terminates the process on Ctrl-C
        # (SIGINT)
        # Note: the following would not be enough to terminate beat and other
        # tasks, which is why the code below explicitly calls sys.exit
        # > from celery.apps.worker import install_worker_term_hard_handler
        # > install_worker_term_hard_handler(self._worker, sig='SIGINT')
        def _shutdown(*args, **kwargs):
            return sys.exit(1)

        platforms.signals["INT"] = _shutdown

        return self._worker


# Signals to the server that the worker is running, see _check_worker in
# CondaStoreServer
@shared_task(base=WorkerTask, name="task_initialize_worker", bind=True)
def task_initialize_worker(self):
    from conda_store_server import orm

    conda_store = self.worker.conda_store

    with conda_store.session_factory() as db:
        db.add(orm.Worker(initialized=True))
        db.commit()


@shared_task(base=WorkerTask, name="task_watch_paths", bind=True)
def task_watch_paths(self):
    conda_store = self.worker.conda_store

    with conda_store.session_factory() as db:
        settings = conda_store.get_settings(db)

        conda_store.configuration(db).update_storage_metrics(
            db, conda_store.store_directory
        )

        environment_paths = environment.discover_environments(self.worker.watch_paths)
        for path in environment_paths:
            with open(path) as f:
                conda_store.register_environment(
                    db,
                    specification=yaml.safe_load(f),
                    namespace=settings.filesystem_namespace,
                    force=False,
                )


@shared_task(base=WorkerTask, name="task_update_storage_metrics", bind=True)
def task_update_storage_metrics(self):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        conda_store.configuration(db).update_storage_metrics(
            db, conda_store.store_directory
        )


@shared_task(base=WorkerTask, name="task_cleanup_builds", bind=True)
def task_cleanup_builds(
    self,
    build_ids: typing.List[str] = None,
    reason: str = None,
    is_canceled: bool = False,
):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        build_cleanup(db, conda_store, build_ids, reason, is_canceled)


"""
Pierre - May 29th 2022
This is a different version of task_update_conda_channels.
It's designed to run one task per channel, with a lock to avoid triggering twice a task for a given channel.
Two scenarios :
- either you're using Redis (that should be the case if you have multiple celery workers) : then the lock is handled by Redis.
- either you don't (that's fine if you're using a single celery worker) : then the lock is a Filelock

The reason behind having the task running only once at a time is
to avoid integrity exceptions when running channel.update_packages.

Sources :
Lock : http://loose-bits.com/2010/10/distributed-task-locking-in-celery.html
Redis : https://pypi.org/project/redis/
https://stackoverflow.com/questions/12003221/celery-task-schedule-ensuring-a-task-is-only-executed-one-at-a-time

"""


@shared_task(base=WorkerTask, name="task_update_conda_channels", bind=True)
def task_update_conda_channels(self):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        conda_store.ensure_conda_channels(db)
        for channel in api.list_conda_channels(db):
            send_task("task_update_conda_channel", args=[channel.name], kwargs={})


@shared_task(base=WorkerTask, name="task_update_conda_channel", bind=True)
def task_update_conda_channel(self, channel_name):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        settings = conda_store.get_settings(db)

        # sanitize the channel name as it's an URL, and it's used for the lock.
        sanitizing = {
            "https": "",
            "http": "",
            ":": "",
            "/": "_",
            "?": "",
            "&": "_",
            "=": "_",
        }
        channel_name_sanitized = channel_name
        for k, v in sanitizing.items():
            channel_name_sanitized = channel_name_sanitized.replace(k, v)

        task_key = f"lock_{self.name}_{channel_name_sanitized}"

        is_locked = False

        if conda_store.redis_url is not None:
            lock = conda_store.redis.lock(task_key, timeout=60 * 15)  # timeout 15min
        else:
            lockfile_path = os.path.join(f"/tmp/task_lock_{task_key}")
            lock = FileLock(lockfile_path, timeout=60 * 15)

        try:
            is_locked = lock.acquire(blocking=False)

            if is_locked:
                channel = api.get_conda_channel(db, channel_name)

                conda_store.log.debug(f"updating packages for channel {channel.name}")
                channel.update_packages(db, subdirs=settings.conda_platforms)

            else:
                conda_store.log.debug(
                    f"skipping updating packages for channel {channel_name} - already in progress"
                )

        except TimeoutError:
            if conda_store.redis_url is None:
                conda_store.log.warning(
                    f"Timeout when acquiring lock with key {task_key} - We assume the task is already being run"
                )
                is_locked = False

        finally:
            if is_locked:
                lock.release()


@shared_task(base=WorkerTask, name="task_solve_conda_environment", bind=True)
def task_solve_conda_environment(self, solve_id):
    conda_store = self.worker.conda_store

    with conda_store.session_factory() as db:
        solve = api.get_solve(db, solve_id)
        solve_conda_environment(db, conda_store, solve)


@shared_task(base=WorkerTask, name="task_build_conda_environment", bind=True)
def task_build_conda_environment(self, build_id):
    conda_store = self.worker.conda_store

    with conda_store.session_factory() as db:
        build = api.get_build(db, build_id)
        build_conda_environment(db, conda_store, build)


@shared_task(base=WorkerTask, name="task_build_conda_env_export", bind=True)
def task_build_conda_env_export(self, build_id):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        build = api.get_build(db, build_id)
        build_conda_env_export(db, conda_store, build)


@shared_task(base=WorkerTask, name="task_build_conda_pack", bind=True)
def task_build_conda_pack(self, build_id):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        build = api.get_build(db, build_id)
        build_conda_pack(db, conda_store, build)


@shared_task(base=WorkerTask, name="task_build_conda_docker", bind=True)
def task_build_conda_docker(self, build_id):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        build = api.get_build(db, build_id)
        build_conda_docker(db, conda_store, build)


@shared_task(base=WorkerTask, name="task_build_constructor_installer", bind=True)
def task_build_constructor_installer(self, build_id):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        build = api.get_build(db, build_id)
        build_constructor_installer(db, conda_store, build)


@shared_task(base=WorkerTask, name="task_update_environment_build", bind=True)
def task_update_environment_build(self, environment_id):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        environment = api.get_environment(db, id=environment_id)

        conda_prefix = environment.current_build.build_path(conda_store)
        environment_prefix = environment.current_build.environment_path(conda_store)

        utils.symlink(conda_prefix, environment_prefix)

        if conda_store.post_update_environment_build_hook:
            conda_store.post_update_environment_build_hook(conda_store, environment)


def delete_build_artifact(db: Session, conda_store, build_artifact):
    if build_artifact.artifact_type == schema.BuildArtifactType.DIRECTORY:
        # ignore key
        conda_prefix = build_artifact.build.build_path(conda_store)
        # be REALLY sure this is a directory within store directory
        if str(conda_prefix).startswith(conda_store.store_directory) and os.path.isdir(
            conda_prefix
        ):
            shutil.rmtree(conda_prefix)
            db.delete(build_artifact)
    elif build_artifact.artifact_type == schema.BuildArtifactType.CONTAINER_REGISTRY:
        pass
        # # container registry tag deletion is not generally implemented
        # # the underlying library `python_docker` is already capable
        # conda_store.container_registry.delete_image(build_artifact.key)
    else:
        conda_store.log.info(f"deleting {build_artifact.key}")
        conda_store.storage.delete(db, build_artifact.build.id, build_artifact.key)


@shared_task(base=WorkerTask, name="task_delete_build", bind=True)
def task_delete_build(self, build_id):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        settings = conda_store.get_settings(db)

        build = api.get_build(db, build_id)

        # Deletes build artifacts for this build
        conda_store.log.info(f"deleting artifacts for build={build.id}")
        for build_artifact in api.list_build_artifacts(
            db,
            build_id=build_id,
            excluded_artifact_types=settings.build_artifacts_kept_on_deletion,
        ).all():
            delete_build_artifact(db, conda_store, build_artifact)

        # Updates build size and marks build as deleted
        build.deleted_on = datetime.datetime.utcnow()
        build.size = 0

        db.commit()


@shared_task(base=WorkerTask, name="task_delete_environment", bind=True)
def task_delete_environment(self, environment_id):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        environment = api.get_environment(db, id=environment_id)

        for build in environment.builds:
            conda_store.log.info(f"deleting artifacts for build={build.id}")
            for build_artifact in api.list_build_artifacts(
                db,
                build_id=build.id,
            ).all():
                delete_build_artifact(db, conda_store, build_artifact)

        db.delete(environment)
        db.commit()


@shared_task(base=WorkerTask, name="task_delete_namespace", bind=True)
def task_delete_namespace(self, namespace_id):
    conda_store = self.worker.conda_store
    with conda_store.session_factory() as db:
        namespace = api.get_namespace(db, id=namespace_id)

        for environment_orm in namespace.environments:
            for build in environment_orm.builds:
                conda_store.log.info(f"deleting artifacts for build={build.id}")
                for build_artifact in api.list_build_artifacts(
                    db,
                    build_id=build.id,
                ).all():
                    delete_build_artifact(db, conda_store, build_artifact)
            db.delete(environment_orm)
        db.delete(namespace)
        db.commit()
