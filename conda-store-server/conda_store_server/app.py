import datetime
import os
import sys
from contextlib import contextmanager
from typing import Any, Dict

import pydantic
from celery import Celery, group
from conda_store_server import (
    CONDA_STORE_DIR,
    BuildKey,
    api,
    conda_utils,
    environment,
    orm,
    registry,
    schema,
    storage,
    utils,
)
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from traitlets import (
    Bool,
    Callable,
    Integer,
    List,
    TraitError,
    Type,
    Unicode,
    Union,
    default,
    validate,
)
from traitlets.config import LoggingConfigurable


def conda_store_validate_specification(
    db: Session,
    conda_store: "CondaStore",
    namespace: str,
    specification: schema.CondaSpecification,
) -> schema.CondaSpecification:
    settings = conda_store.get_settings(
        db, namespace=namespace, environment_name=specification.name
    )

    specification = environment.validate_environment_channels(specification, settings)
    specification = environment.validate_environment_pypi_packages(
        specification, settings
    )
    specification = environment.validate_environment_conda_packages(
        specification, settings
    )

    return specification


def conda_store_validate_action(
    db: Session,
    conda_store: "CondaStore",
    namespace: str,
    action: schema.Permissions,
) -> None:
    settings = conda_store.get_settings(db)
    system_metrics = api.get_system_metrics(db)

    if action in (
        schema.Permissions.ENVIRONMENT_CREATE,
        schema.Permissions.ENVIRONMENT_UPDATE,
    ) and (settings.storage_threshold > system_metrics.disk_free):
        raise utils.CondaStoreError(
            f"`CondaStore.storage_threshold` reached. Action {action.value} prevented due to insufficient storage space"
        )


class CondaStore(LoggingConfigurable):
    storage_class = Type(
        default_value=storage.LocalStorage,
        klass=storage.Storage,
        allow_none=False,
        config=True,
    )

    container_registry_class = Type(
        default_value=registry.ContainerRegistry,
        klass=registry.ContainerRegistry,
        allow_none=False,
        config=True,
    )

    store_directory = Unicode(
        str(CONDA_STORE_DIR / "state"),
        help="directory for conda-store to build environments and store state",
        config=True,
    )

    build_directory = Unicode(
        "{store_directory}/{namespace}",
        help="Template used to form the directory for storing conda environment builds. Available keys: store_directory, namespace, name. The default will put all built environments in the same namespace within the same directory.",
        config=True,
    )

    environment_directory = Unicode(
        "{store_directory}/{namespace}/envs/{name}",
        help="Template used to form the directory for symlinking conda environment builds. Available keys: store_directory, namespace, name. The default will put all environments in the same namespace within the same directory.",
        config=True,
    )

    build_key_version = Integer(
        BuildKey.set_current_version(2),
        help="Build key version to use: 1 (long, legacy), 2 (short, default)",
        config=True,
    )

    @validate("build_key_version")
    def _check_build_key_version(self, proposal):
        try:
            return BuildKey.set_current_version(proposal.value)
        except Exception as e:
            raise TraitError(f"c.CondaStore.build_key_version: {e}")

    win_extended_length_prefix = Bool(
        False,
        help="Use the extended-length prefix '\\\\?\\' (Windows-only), default: False",
        config=True,
    )

    conda_command = Unicode(
        "mamba",
        help="conda executable to use for solves",
        config=True,
    )

    conda_solve_platforms = List(
        [conda_utils.conda_platform()],
        description="Conda platforms to solve environments for via conda-lock. Must include current platform.",
        config=True,
    )

    conda_channel_alias = Unicode(
        "https://conda.anaconda.org",
        help="The prepended url location to associate with channel names",
        config=True,
    )

    conda_platforms = List(
        [conda_utils.conda_platform(), "noarch"],
        help="Conda platforms to download package repodata.json from. By default includes current architecture and noarch",
        config=True,
    )

    conda_default_channels = List(
        ["conda-forge"],
        help="Conda channels that by default are included if channels are empty",
        config=True,
    )

    conda_allowed_channels = List(
        [],
        help=(
            "Allowed conda channels to be used in conda environments. "
            "If set to empty list all channels are accepted (default). "
            "Example: "
            '["main", "conda-forge", "https://repo.anaconda.com/pkgs/main"]'
        ),
        config=True,
    )

    conda_indexed_channels = List(
        ["main", "conda-forge", "https://repo.anaconda.com/pkgs/main"],
        help="Conda channels to be indexed by conda-store at start.  Defaults to main and conda-forge.",
        config=True,
    )

    conda_default_packages = List(
        [],
        help="Conda packages that included by default if none are included",
        config=True,
    )

    conda_required_packages = List(
        [],
        help="Conda packages that are required to be within environment specification. Will raise a validation error is package not in specification",
        config=True,
    )

    conda_included_packages = List(
        [],
        help="Conda packages that auto included within environment specification. Will not raise a validation error if package not in specification and will be auto added",
        config=True,
    )

    pypi_default_packages = List(
        [],
        help="PyPi packages that included by default if none are included",
        config=True,
    )

    pypi_required_packages = List(
        [],
        help="PyPi packages that are required to be within environment specification. Will raise a validation error is package not in specification",
        config=True,
    )

    pypi_included_packages = List(
        [],
        help="PyPi packages that auto included within environment specification. Will not raise a validation error if package not in specification and will be auto added",
        config=True,
    )

    conda_max_solve_time = Integer(
        5 * 60,  # 5 minute
        help="Maximum time in seconds to allow for solving a given conda environment",
        config=True,
    )

    storage_threshold = Integer(
        5 * 1024**3,  # 5 GB
        help="Storage threshold in bytes of minimum available storage required in order to perform builds",
        config=True,
    )

    database_url = Unicode(
        "sqlite:///" + str(CONDA_STORE_DIR / "conda-store.sqlite"),
        help="url for the database. e.g. 'sqlite:///conda-store.sqlite' tables will be automatically created if they do not exist",
        config=True,
    )

    upgrade_db = Bool(
        True,
        help="""Upgrade the database automatically on start.
        Only safe if database is regularly backed up.
        """,
        config=True,
    )

    redis_url = Unicode(
        None,
        help="Redis connection url in form 'redis://:<password>@<hostname>:<port>/0'. Connection is used by Celery along with conda-store internally",
        config=True,
        allow_none=True,
    )

    @validate("redis_url")
    def _check_redis(self, proposal):
        try:
            if self.redis_url is not None:
                self.redis.ping()
        except Exception:
            raise TraitError(
                f'c.CondaStore.redis_url unable to connect with Redis database at "{self.redis_url}"'
            )
        return proposal.value

    celery_broker_url = Unicode(
        help="broker url to use for celery tasks",
        config=True,
    )

    build_artifacts = List(
        [
            schema.BuildArtifactType.LOCKFILE,
            schema.BuildArtifactType.YAML,
            schema.BuildArtifactType.CONDA_PACK,
            schema.BuildArtifactType.CONSTRUCTOR_INSTALLER,
            *(
                [
                    schema.BuildArtifactType.DOCKER_MANIFEST,
                    schema.BuildArtifactType.CONTAINER_REGISTRY,
                ]
                if sys.platform == "linux"
                else []
            ),
        ],
        help="artifacts to build in conda-store. By default all of the artifacts",
        config=True,
    )

    build_artifacts_kept_on_deletion = List(
        [
            schema.BuildArtifactType.LOGS,
            schema.BuildArtifactType.LOCKFILE,
            schema.BuildArtifactType.YAML,
            # no possible way to delete these artifacts
            # in most container registries via api
            schema.BuildArtifactType.CONTAINER_REGISTRY,
        ],
        help="artifacts to keep on build deletion",
        config=True,
    )

    serialize_builds = Bool(
        True,
        help="DEPRICATED no longer has any effect",
        config=True,
    )

    @default("celery_broker_url")
    def _default_celery_broker_url(self):
        if self.redis_url is not None:
            return self.redis_url
        return f"sqla+{self.database_url}"

    celery_results_backend = Unicode(
        help="backend to use for celery task results",
        config=True,
    )

    @default("celery_results_backend")
    def _default_celery_results_backend(self):
        if self.redis_url is not None:
            return self.redis_url
        return f"db+{self.database_url}"

    default_namespace = Unicode(
        "default", help="default namespace for conda-store", config=True
    )

    filesystem_namespace = Unicode(
        "filesystem",
        help="namespace to use for environments picked up via `CondaStoreWorker.watch_paths` on the filesystem",
        config=True,
    )

    default_uid = Integer(
        None if sys.platform == "win32" else os.getuid(),
        help="default uid to assign to built environments",
        config=True,
        allow_none=True,
    )

    default_gid = Integer(
        None if sys.platform == "win32" else os.getgid(),
        help="default gid to assign to built environments",
        config=True,
        allow_none=True,
    )

    default_permissions = Unicode(
        None if sys.platform == "win32" else "775",
        help="default file permissions to assign to built environments",
        config=True,
        allow_none=True,
    )

    default_docker_base_image = Union(
        [Unicode(), Callable()],
        help="default base image used for the Dockerized environments. Make sure to have a proper glibc within image (highly discourage alpine/musl based images). Can also be callable function which takes the `orm.Build` object as input which has access to all attributes about the build such as install packages, requested packages, name, namespace, etc",
        config=True,
    )

    @default("default_docker_base_image")
    def _default_docker_base_image(self):
        def _docker_base_image(build: orm.Build):
            return "registry-1.docker.io/library/debian:sid-slim"

        return _docker_base_image

    validate_specification = Callable(
        conda_store_validate_specification,
        help="callable function taking conda_store, namespace, and specification as input arguments to apply for validating and modifying a given specification. If there are validation issues with the environment ValueError with message should be raised. If changed you may need to call the default function to preseve many of the trait effects e.g. `c.CondaStore.default_channels` etc",
        config=True,
    )

    validate_action = Callable(
        conda_store_validate_action,
        help="callable function taking conda_store, namespace, and action. If there are issues with performing the given action raise a CondaStoreError should be raised.",
        config=True,
    )

    post_update_environment_build_hook = Callable(
        default_value=None,
        help="callable function taking conda_store and `orm.Environment` object as input arguments. This function can be used to add custom behavior that will run after an environment's current build changes.",
        config=True,
        allow_none=True,
    )

    @property
    def session_factory(self):
        if hasattr(self, "_session_factory"):
            return self._session_factory

        self._session_factory = orm.new_session_factory(
            url=self.database_url,
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
    def redis(self):
        import redis

        if hasattr(self, "_redis"):
            return self._redis
        self._redis = redis.Redis.from_url(self.redis_url)
        return self._redis

    def configuration(self, db: Session):
        return orm.CondaStoreConfiguration.configuration(db)

    @property
    def storage(self):
        if hasattr(self, "_storage"):
            return self._storage
        self._storage = self.storage_class(parent=self, log=self.log)

        if isinstance(self._storage, storage.LocalStorage):
            os.makedirs(self._storage.storage_path, exist_ok=True)

        return self._storage

    @property
    def container_registry(self):
        if hasattr(self, "_container_registry"):
            return self._container_registry
        self._container_registry = self.container_registry_class(
            parent=self, log=self.log
        )
        return self._container_registry

    @property
    def celery_config(self):
        return {
            "broker_url": self.celery_broker_url,
            "result_backend": self.celery_results_backend,
            "imports": [
                "conda_store_server.worker.tasks",
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

    def ensure_settings(self, db: Session):
        """Ensure that conda-store traitlets settings are applied"""
        settings = schema.Settings(
            default_namespace=self.default_namespace,
            filesystem_namespace=self.filesystem_namespace,
            default_uid=self.default_uid,
            default_gid=self.default_gid,
            default_permissions=self.default_permissions,
            storage_threshold=self.storage_threshold,
            conda_command=self.conda_command,
            conda_platforms=self.conda_platforms,
            conda_max_solve_time=self.conda_max_solve_time,
            conda_indexed_channels=self.conda_indexed_channels,
            build_artifacts_kept_on_deletion=self.build_artifacts_kept_on_deletion,
            conda_solve_platforms=self.conda_solve_platforms,
            conda_channel_alias=self.conda_channel_alias,
            conda_default_channels=self.conda_default_channels,
            conda_allowed_channels=self.conda_allowed_channels,
            conda_default_packages=self.conda_default_packages,
            conda_required_packages=self.conda_required_packages,
            conda_included_packages=self.conda_included_packages,
            pypi_default_packages=self.pypi_default_packages,
            pypi_required_packages=self.pypi_required_packages,
            pypi_included_packages=self.pypi_included_packages,
            build_artifacts=self.build_artifacts,
            # default_docker_base_image=self.default_docker_base_image,
        )
        api.set_kvstore_key_values(db, "setting", settings.dict(), update=False)

    def ensure_namespace(self, db: Session):
        """Ensure that conda-store default namespaces exists"""
        api.ensure_namespace(db, self.default_namespace)

    def ensure_directories(self):
        """Ensure that conda-store filesystem directories exist"""
        os.makedirs(self.store_directory, exist_ok=True)

    def ensure_conda_channels(self, db: Session):
        """Ensure that conda-store indexed channels and packages are in database"""
        self.log.info("updating conda store channels")

        settings = self.get_settings(db)

        for channel in settings.conda_indexed_channels:
            normalized_channel = conda_utils.normalize_channel_name(
                settings.conda_channel_alias, channel
            )
            api.ensure_conda_channel(db, normalized_channel)

    def set_settings(
        self,
        db: Session,
        namespace: str = None,
        environment_name: str = None,
        data: Dict[str, Any] = {},
    ):
        setting_keys = schema.Settings.__fields__.keys()
        if not data.keys() <= setting_keys:
            invalid_keys = data.keys() - setting_keys
            raise ValueError(f"Invalid setting keys {invalid_keys}")

        for key, value in data.items():
            field = schema.Settings.__fields__[key]
            global_setting = field.field_info.extra["metadata"]["global"]
            if global_setting and (
                namespace is not None or environment_name is not None
            ):
                raise ValueError(
                    f"Setting {key} is a global setting cannot be set within namespace or environment"
                )

            try:
                pydantic.parse_obj_as(field.outer_type_, value)
            except Exception as e:
                raise ValueError(
                    f"Invalid parsing of setting {key} expected type {field.outer_type_} ran into error {e}"
                )

        if namespace is not None and environment_name is not None:
            prefix = f"setting/{namespace}/{environment_name}"
        elif namespace is not None:
            prefix = f"setting/{namespace}"
        else:
            prefix = "setting"

        api.set_kvstore_key_values(db, prefix, data)

    def get_settings(
        self, db: Session, namespace: str = None, environment_name: str = None
    ) -> schema.Settings:
        # setting logic is intentionally done in python code
        # rather than using the database for merges and ordering
        # becuase in the future we may likely want to do some
        # more complex logic around settings

        prefixes = ["setting"]
        if namespace is not None:
            prefixes.append(f"setting/{namespace}")
        if namespace is not None and environment_name is not None:
            prefixes.append(f"setting/{namespace}/{environment_name}")

        settings = {}
        for prefix in prefixes:
            settings.update(api.get_kvstore_key_values(db, prefix))

        return schema.Settings(**settings)

    def register_solve(self, db: Session, specification: schema.CondaSpecification):
        """Registers a solve for a given specification"""
        settings = self.get_settings(db)

        self.validate_action(
            db=db,
            conda_store=self,
            namespace="solve",
            action=schema.Permissions.ENVIRONMENT_SOLVE,
        )

        specification_model = self.validate_specification(
            db=db,
            conda_store=self,
            namespace="solve",
            specification=specification,
        )

        specification_orm = api.ensure_specification(db, specification_model)
        solve = api.create_solve(db, specification_orm.id)
        db.commit()

        self.celery_app

        from conda_store_server.worker import tasks

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
    ):
        """Register a given specification to conda store with given namespace/name."""
        settings = self.get_settings(db)

        namespace = namespace or settings.default_namespace
        namespace = api.ensure_namespace(db, name=namespace)

        self.validate_action(
            db=db,
            conda_store=self,
            namespace=namespace.name,
            action=schema.Permissions.ENVIRONMENT_CREATE,
        )

        specification_model = self.validate_specification(
            db=db,
            conda_store=self,
            namespace=namespace.name,
            specification=schema.CondaSpecification.parse_obj(specification),
        )

        spec_sha256 = utils.datastructure_hash(specification_model.dict())
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

        specification = api.ensure_specification(db, specification_model)
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
        self.validate_action(
            db=db,
            conda_store=self,
            namespace=environment.namespace.name,
            action=schema.Permissions.ENVIRONMENT_UPDATE,
        )

        settings = self.get_settings(
            db, namespace=environment.namespace.name, environment_name=environment.name
        )

        specification = api.get_specification(db, specification_sha256)
        build = api.create_build(
            db, environment_id=environment_id, specification_id=specification.id
        )
        db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

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

        if (
            schema.BuildArtifactType.DOCKER_MANIFEST in settings.build_artifacts
            or schema.BuildArtifactType.CONTAINER_REGISTRY in settings.build_artifacts
        ):
            artifact_tasks.append(
                tasks.task_build_conda_docker.subtask(
                    args=(build.id,), task_id=f"build-{build.id}-docker", immutable=True
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
        self.validate_action(
            db=db,
            conda_store=self,
            namespace=namespace,
            action=schema.Permissions.ENVIRONMENT_UPDATE,
        )

        build = api.get_build(db, build_id)
        if build is None:
            raise utils.CondaStoreError(f"build id={build_id} does not exist")

        environment = api.get_environment(db, namespace=namespace, name=name)
        if environment is None:
            raise utils.CondaStoreError(
                f"environment namespace={namespace} name={name} does not exist"
            )

        if build.status != schema.BuildStatus.COMPLETED:
            raise utils.CondaStoreError(
                "cannot update environment to build id since not completed"
            )

        if build.specification.name != name:
            raise utils.CondaStoreError(
                "cannot update environment to build id since specification does not match environment name"
            )

        environment.current_build_id = build.id
        db.commit()

        self.celery_app
        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        tasks.task_update_environment_build.si(environment.id).apply_async()

    def update_environment_description(
        self, db: Session, namespace: str, name: str, description: str
    ):
        environment = api.get_environment(db, namespace=namespace, name=name)
        if environment is None:
            raise utils.CondaStoreError(
                f"environment namespace={namespace} name={name} does not exist"
            )

        environment.description = description
        db.commit()

    def delete_namespace(self, db: Session, namespace: str):
        self.validate_action(
            db=db,
            conda_store=self,
            namespace=namespace,
            action=schema.Permissions.NAMESPACE_DELETE,
        )

        namespace = api.get_namespace(db, name=namespace)
        if namespace is None:
            raise utils.CondaStoreError(f"namespace={namespace} does not exist")

        utcnow = datetime.datetime.utcnow()
        namespace.deleted_on = utcnow
        for environment_orm in namespace.environments:
            environment_orm.deleted_on = utcnow
            for build in environment_orm.builds:
                build.deleted_on = utcnow
        db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        tasks.task_delete_namespace.si(namespace.id).apply_async()

    def delete_environment(self, db: Session, namespace: str, name: str):
        self.validate_action(
            db=db,
            conda_store=self,
            namespace=namespace,
            action=schema.Permissions.ENVIRONMENT_DELETE,
        )

        environment = api.get_environment(db, namespace=namespace, name=name)
        if environment is None:
            raise utils.CondaStoreError(
                f"environment namespace={namespace} name={name} does not exist"
            )

        utcnow = datetime.datetime.utcnow()
        environment.deleted_on = utcnow
        for build in environment.builds:
            build.deleted_on = utcnow
        db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        tasks.task_delete_environment.si(environment.id).apply_async()

    def delete_build(self, db: Session, build_id: int):
        build = api.get_build(db, build_id)

        self.validate_action(
            db=db,
            conda_store=self,
            namespace=build.environment.namespace.name,
            action=schema.Permissions.BUILD_DELETE,
        )

        if build.status not in [
            schema.BuildStatus.FAILED,
            schema.BuildStatus.COMPLETED,
        ]:
            raise utils.CondaStoreError(
                "cannot delete build since not finished building"
            )

        build.deleted_on = datetime.datetime.utcnow()
        db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        tasks.task_delete_build.si(build.id).apply_async()
