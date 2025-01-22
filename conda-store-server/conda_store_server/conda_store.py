# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import datetime
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict

from celery import Celery, group
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from conda_store_server import CONDA_STORE_DIR, api, conda_store_config, storage
from conda_store_server._internal import conda_utils, orm, schema, settings, utils
from conda_store_server.exception import CondaStoreError
from conda_store_server.plugins import hookspec, plugin_manager
from conda_store_server.plugins.types import lock
from conda_store_server.server import schema as auth_schema


class CondaStore:
    """This class provides a set of common functionality to be used by
    conda store servers and workers.

    Attributes
    ----------
    config : conda_store_config.CondaStore
        CondaStore config object. This config object has global config
        that is applied to both servers and workers.
    log : logging.Logger
        global logger
    """

    def __init__(self, config: conda_store_config.CondaStore):
        self.config = config
        self.log = logging.getLogger(__name__)

    @property
    def session_factory(self) -> sessionmaker:
        if hasattr(self, "_session_factory"):
            return self._session_factory

        self._session_factory = orm.new_session_factory(
            url=self.config.database_url,
            poolclass=QueuePool,
        )

        return self._session_factory

    # Do not define this as a FastAPI dependency! That would cause Sessions
    # not to be closed, which would lead to DB pool exhaustion and requests
    # getting blocked.
    # https://github.com/conda-incubator/conda-store/issues/598
    @contextmanager
    def get_db(self):
        db = self.session_factory()
        try:
            yield db
        finally:
            db.close()

    @property
    def settings(self):
        if hasattr(self, "_settings"):
            return self._settings

        with self.get_db() as db:
            # setup the setting object with a session. Once this block finishes
            # excuting, the db session will close. By default in sqlalchemy, this
            # will release the connection, however, the connection may be restablished.
            # ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#closing
            self._settings = settings.Settings(
                db=db, deployment_default=schema.Settings(**self.config.trait_values())
            )
        return self._settings

    @property
    def redis(self):
        import redis

        if hasattr(self, "_redis"):
            return self._redis
        self._redis = redis.Redis.from_url(self.config.redis_url)
        return self._redis

    def configuration(self, db: Session):
        return orm.CondaStoreConfiguration.configuration(db)

    @property
    def storage(self):
        if hasattr(self, "_storage"):
            return self._storage
        self._storage = self.config.storage_class(parent=self.config, log=self.log)

        if isinstance(self._storage, storage.LocalStorage):
            os.makedirs(self._storage.storage_path, exist_ok=True)

        return self._storage

    @property
    def celery_config(self):
        return {
            "broker_url": self.config.celery_broker_url,
            "result_backend": self.config.celery_results_backend,
            "imports": [
                "conda_store_server._internal.worker.tasks",
                "celery.contrib.testing.tasks",
            ],
            "task_track_started": True,
            "result_extended": True,
            "beat_schedule": {
                "watch-paths": {
                    "task": "task_watch_paths",
                    "schedule": 60.0,  # 1 minute
                    "args": [],
                    "kwargs": {},
                },
                "update-conda-channels": {
                    "task": "task_update_conda_channels",
                    "schedule": 15.0 * 60.0,  # 15 minutes
                    "args": [],
                    "kwargs": {},
                },
            },
            "beat_schedule_filename": str(CONDA_STORE_DIR / "celerybeat-schedule"),
            "triatlets": {},
        }

    @property
    def celery_app(self):
        # if hasattr(self, "_celery_app"):
        #     return self._celery_app

        self._celery_app = Celery("tasks")
        self._celery_app.config_from_object(self.celery_config)
        return self._celery_app

    @property
    def plugin_manager(self):
        """Creates a plugin manager (if it doesn't already exist) and registers all plugins"""
        if hasattr(self, "_plugin_manager"):
            return self._plugin_manager

        self._plugin_manager = plugin_manager.PluginManager(hookspec.spec_name)
        self._plugin_manager.add_hookspecs(hookspec.CondaStoreSpecs)

        # Register all available plugins
        self._plugin_manager.collect_plugins()

        return self._plugin_manager

    def lock_plugin(self) -> tuple[str, lock.LockPlugin]:
        """Returns the configured lock plugin"""
        # TODO: get configured lock plugin name from settings
        lock_plugin = self.plugin_manager.get_lock_plugin(name=self.config.lock_backend)
        locker = lock_plugin.backend()
        return lock_plugin.name, locker

    def ensure_namespace(self, db: Session):
        """Ensure that conda-store default namespaces exists"""
        api.ensure_namespace(db, self.config.default_namespace)

    def ensure_directories(self):
        """Ensure that conda-store filesystem directories exist"""
        os.makedirs(self.config.store_directory, exist_ok=True)

    def ensure_conda_channels(self, db: Session):
        """Ensure that conda-store indexed channels and packages are
        in database. Only globally defined `conda_indexed_channels`
        with the globally defined `conda_channel_alias` will be indexed
        """
        self.log.info("updating conda store channels")

        settings = self.get_settings()

        for channel in settings.conda_indexed_channels:
            normalized_channel = conda_utils.normalize_channel_name(
                settings.conda_channel_alias, channel
            )
            api.ensure_conda_channel(db, normalized_channel)

    def set_settings(
        self,
        namespace: str = None,
        environment_name: str = None,
        data: Dict[str, Any] = {},
    ):
        return self.settings.set_settings(
            namespace=namespace, environment_name=environment_name, data=data
        )

    def get_settings(
        self, namespace: str = None, environment_name: str = None
    ) -> schema.Settings:
        return self.settings.get_settings(
            namespace=namespace, environment_name=environment_name
        )

    def get_setting(
        self, key: str, namespace: str = None, environment_name: str = None
    ) -> schema.Settings:
        return self.settings.get_setting(
            key=key, namespace=namespace, environment_name=environment_name
        )

    def register_solve(self, db: Session, specification: schema.CondaSpecification):
        """Registers a solve for a given specification"""
        settings = self.get_settings()

        self.config.validate_action(
            db=db,
            conda_store=self,
            namespace="solve",
            action=auth_schema.Permissions.ENVIRONMENT_SOLVE,
        )

        specification_model = self.config.validate_specification(
            db=db,
            conda_store=self,
            namespace="solve",
            specification=specification,
        )

        specification_orm = api.ensure_specification(db, specification_model)
        solve = api.create_solve(db, specification_orm.id)
        db.commit()

        self.celery_app

        from conda_store_server._internal.worker import tasks

        task_id = f"solve-{solve.id}"
        tasks.task_solve_conda_environment.apply_async(
            args=[solve.id],
            time_limit=settings.conda_max_solve_time,
            task_id=task_id,
        )

        return task_id, solve.id

    def register_environment(
        self,
        db: Session,
        specification: dict,
        namespace: str = None,
        force: bool = True,
        is_lockfile: bool = False,
    ):
        """Register a given specification to conda store with given namespace/name."""
        namespace = namespace or self.get_setting("default_namespace")
        namespace = api.ensure_namespace(db, name=namespace)

        self.config.validate_action(
            db=db,
            conda_store=self,
            namespace=namespace.name,
            action=auth_schema.Permissions.ENVIRONMENT_CREATE,
        )

        if is_lockfile:
            # It's a lockfile, do not do any validation in this case. If there
            # are problems, these would be caught earlier during parsing or
            # later when conda-lock attempts to install it.
            specification_model = specification
        else:
            specification_model = self.config.validate_specification(
                db=db,
                conda_store=self,
                namespace=namespace.name,
                specification=schema.CondaSpecification.model_validate(specification),
            )

        spec_sha256 = utils.datastructure_hash(specification_model.model_dump())
        matching_specification = api.get_specification(db, sha256=spec_sha256)
        if (
            matching_specification is not None
            and not force
            and any(
                _.environment.namespace.id == namespace.id
                for _ in matching_specification.builds
            )
        ):
            return None

        specification = api.ensure_specification(
            db, specification_model, is_lockfile=is_lockfile
        )
        environment_was_empty = (
            api.get_environment(db, name=specification.name, namespace_id=namespace.id)
            is None
        )
        environment = api.ensure_environment(
            db,
            name=specification.name,
            namespace_id=namespace.id,
            description=specification.spec["description"],
        )

        build = self.create_build(db, environment.id, specification.sha256)

        if environment_was_empty:
            environment.current_build = build
            db.commit()

        return build.id

    def create_build(self, db: Session, environment_id: int, specification_sha256: str):
        environment = api.get_environment(db, id=environment_id)
        self.config.validate_action(
            db=db,
            conda_store=self,
            namespace=environment.namespace.name,
            action=auth_schema.Permissions.ENVIRONMENT_UPDATE,
        )

        settings = self.get_settings(
            namespace=environment.namespace.name, environment_name=environment.name
        )

        specification = api.get_specification(db, specification_sha256)
        build = api.create_build(
            db, environment_id=environment_id, specification_id=specification.id
        )
        db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server._internal.worker import tasks

        # Note: task ids used here must also be in api_put_build_cancel

        artifact_tasks = []
        if schema.BuildArtifactType.YAML in settings.build_artifacts:
            artifact_tasks.append(
                tasks.task_build_conda_env_export.subtask(
                    args=(build.id,),
                    task_id=f"build-{build.id}-conda-env-export",
                    immutable=True,
                )
            )
        if schema.BuildArtifactType.CONDA_PACK in settings.build_artifacts:
            artifact_tasks.append(
                tasks.task_build_conda_pack.subtask(
                    args=(build.id,),
                    task_id=f"build-{build.id}-conda-pack",
                    immutable=True,
                )
            )

        if schema.BuildArtifactType.CONSTRUCTOR_INSTALLER in settings.build_artifacts:
            artifact_tasks.append(
                tasks.task_build_constructor_installer.subtask(
                    args=(build.id,),
                    task_id=f"build-{build.id}-constructor-installer",
                    immutable=True,
                )
            )

        (
            tasks.task_update_storage_metrics.si()
            | tasks.task_build_conda_environment.subtask(
                args=(build.id,),
                task_id=f"build-{build.id}-environment",
                immutable=True,
            )
            | group(*artifact_tasks)
            | tasks.task_update_storage_metrics.si()
        ).apply_async(task_id=f"build-{build.id}")

        return build

    def update_environment_build(
        self, db: Session, namespace: str, name: str, build_id: int
    ):
        self.config.validate_action(
            db=db,
            conda_store=self,
            namespace=namespace,
            action=auth_schema.Permissions.ENVIRONMENT_UPDATE,
        )

        build = api.get_build(db, build_id)
        if build is None:
            raise CondaStoreError(f"build id={build_id} does not exist")

        environment = api.get_environment(db, namespace=namespace, name=name)
        if environment is None:
            raise CondaStoreError(
                f"environment namespace={namespace} name={name} does not exist"
            )

        if build.status != schema.BuildStatus.COMPLETED:
            raise CondaStoreError(
                "cannot update environment to build id since not completed"
            )

        if build.specification.name != name:
            raise CondaStoreError(
                "cannot update environment to build id since specification does not match environment name"
            )

        environment.current_build_id = build.id
        db.commit()

        self.celery_app
        # must import tasks after a celery app has been initialized
        from conda_store_server._internal.worker import tasks

        tasks.task_update_environment_build.si(environment.id).apply_async()

    def update_environment_description(
        self, db: Session, namespace: str, name: str, description: str
    ):
        environment = api.get_environment(db, namespace=namespace, name=name)
        if environment is None:
            raise CondaStoreError(
                f"environment namespace={namespace} name={name} does not exist"
            )

        environment.description = description
        db.commit()

    def delete_namespace(self, db: Session, namespace: str):
        self.config.validate_action(
            db=db,
            conda_store=self,
            namespace=namespace,
            action=auth_schema.Permissions.NAMESPACE_DELETE,
        )

        namespace = api.get_namespace(db, name=namespace)
        if namespace is None:
            raise CondaStoreError(f"namespace={namespace} does not exist")

        utcnow = datetime.datetime.utcnow()
        namespace.deleted_on = utcnow
        for environment_orm in namespace.environments:
            environment_orm.deleted_on = utcnow
            for build in environment_orm.builds:
                build.deleted_on = utcnow
        db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server._internal.worker import tasks

        tasks.task_delete_namespace.si(namespace.id).apply_async()

    def delete_environment(self, db: Session, namespace: str, name: str):
        self.config.validate_action(
            db=db,
            conda_store=self,
            namespace=namespace,
            action=auth_schema.Permissions.ENVIRONMENT_DELETE,
        )

        environment = api.get_environment(db, namespace=namespace, name=name)
        if environment is None:
            raise CondaStoreError(
                f"environment namespace={namespace} name={name} does not exist"
            )

        utcnow = datetime.datetime.utcnow()
        environment.deleted_on = utcnow
        for build in environment.builds:
            build.deleted_on = utcnow
        db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server._internal.worker import tasks

        tasks.task_delete_environment.si(environment.id).apply_async()

    def delete_build(self, db: Session, build_id: int):
        build = api.get_build(db, build_id)

        self.config.validate_action(
            db=db,
            conda_store=self,
            namespace=build.environment.namespace.name,
            action=auth_schema.Permissions.BUILD_DELETE,
        )

        if build.status not in [
            schema.BuildStatus.FAILED,
            schema.BuildStatus.COMPLETED,
        ]:
            raise CondaStoreError("cannot delete build since not finished building")

        build.deleted_on = datetime.datetime.utcnow()
        db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server._internal.worker import tasks

        tasks.task_delete_build.si(build.id).apply_async()
