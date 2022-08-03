import os
import datetime

import redis
from celery import Celery, group
from traitlets import (
    Type,
    Unicode,
    Integer,
    List,
    default,
    Callable,
    Bool,
    validate,
    TraitError,
)
from traitlets.config import LoggingConfigurable
from sqlalchemy.pool import NullPool

from conda_store_server import orm, utils, storage, schema, api, conda, environment


def conda_store_validate_specification(
    conda_store: "CondaStore", namespace: str, specification: schema.CondaSpecification
) -> schema.CondaSpecification:
    specification = environment.validate_environment_channels(
        specification,
        conda_store.conda_channel_alias,
        conda_store.conda_default_channels,
        conda_store.conda_allowed_channels,
    )

    specification = environment.validate_environment_pypi_packages(
        specification,
        conda_store.pypi_default_packages,
        conda_store.pypi_included_packages,
        conda_store.pypi_required_packages,
    )

    specification = environment.validate_environment_conda_packages(
        specification,
        conda_store.conda_default_packages,
        conda_store.conda_included_packages,
        conda_store.conda_required_packages,
    )

    return specification


class CondaStore(LoggingConfigurable):
    storage_class = Type(
        default_value=storage.S3Storage,
        klass=storage.Storage,
        allow_none=False,
        config=True,
    )

    store_directory = Unicode(
        "conda-store-state",
        help="directory for conda-store to build environments and store state",
        config=True,
    )

    build_directory = Unicode(
        "{store_directory}/{namespace}",
        help="Template used to form the directory for storing conda environment builds. Available keys: store_directory, namespace, name. The default will put all built environments in the same namespace within the same directory.",
        config=True,
    )

    environment_directory = Unicode(
        "{store_directory}/{namespace}/envs",
        help="Template used to form the directory for symlinking conda environment builds. Available keys: store_directory, namespace, name. The default will put all environments in the same namespace within the same directory.",
        config=True,
    )

    conda_command = Unicode(
        "mamba",
        help="conda executable to use for solves",
        config=True,
    )

    conda_channel_alias = Unicode(
        "https://conda.anaconda.org",
        help="The prepended url location to associate with channel names",
        config=True,
    )

    conda_platforms = List(
        [conda.conda_platform(), "noarch"],
        help="Conda platforms to download package repodata.json from. By default includes current architecture and noarch",
        config=True,
    )

    conda_default_channels = List(
        ["conda-forge"],
        help="Conda channels that by default are included if channels are empty",
        config=True,
    )

    conda_allowed_channels = List(
        [
            "main",
            "conda-forge",
            "https://repo.anaconda.com/pkgs/main",
        ],
        help="Allowed conda channels to be used in conda environments. If set to empty list all channels are accepted. Defaults to main and conda-forge",
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

    database_url = Unicode(
        "sqlite:///conda-store.sqlite",
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
        help="Redis connection url in form 'redis://:<password>@<hostname>:<port>/0'. Connection is used by Celery along with conda-store internally",
        config=True,
    )

    @default("redis_url")
    def _default_redis(self):
        raise TraitError("c.CondaStore.redis_url Redis connection url is required")

    @validate("redis_url")
    def _check_redis(self, proposal):
        try:
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
            schema.BuildArtifactType.DOCKER_MANIFEST,
        ],
        help="artifacts to build in conda-store. By default all of the artifacts",
        config=True,
    )

    build_artifacts_kept_on_deletion = List(
        [
            schema.BuildArtifactType.LOGS,
            schema.BuildArtifactType.LOCKFILE,
            schema.BuildArtifactType.YAML,
        ],
        help="artifacts to keep on build deletion",
        config=True,
    )

    serialize_builds = Bool(
        True,
        help="No longer build conda environment in parallel. This is due to an issue in conda/mamba that when downloading files in two concurent builds the downloads/extraction can overlap. This is a bug in conda/mamba that needs to be fixed.",
        config=True,
    )

    @default("celery_broker_url")
    def _default_celery_broker_url(self):
        return self.redis_url

    celery_results_backend = Unicode(
        help="backend to use for celery task results",
        config=True,
    )

    @default("celery_results_backend")
    def _default_celery_results_backend(self):
        return self.redis_url

    default_namespace = Unicode(
        "default", help="default namespace for conda-store", config=True
    )

    filesystem_namespace = Unicode(
        "filesystem",
        help="namespace to use for environments picked up via `CondaStoreWorker.watch_paths` on the filesystem",
        config=True,
    )

    default_uid = Integer(
        os.getuid(),
        help="default uid to assign to built environments",
        config=True,
    )

    default_gid = Integer(
        os.getgid(),
        help="default gid to assign to built environments",
        config=True,
    )

    default_permissions = Unicode(
        "775",
        help="default file permissions to assign to built environments",
        config=True,
    )

    default_docker_base_image = Unicode(
        "library/debian:sid-slim",
        help="default base image used for the Dockerized environments. Make sure to have a proper glibc within image.",
        config=True,
    )

    validate_specification = Callable(
        conda_store_validate_specification,
        help="callable function taking conda_store and specification as input arguments to apply for validating and modifying a given specification. If there are validation issues with the environment ValueError with message should be raised. If changed you may need to call the default function to preseve many of the trait effects e.g. `c.CondaStore.default_channels` etc",
        config=True,
    )

    @property
    def session_factory(self):
        if hasattr(self, "_session_factory"):
            return self._session_factory

        # https://docs.sqlalchemy.org/en/14/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork
        # This is the most simplistic, one shot system that prevents
        # the Engine from using any connection more than once
        self._session_factory = orm.new_session_factory(
            url=self.database_url, poolclass=NullPool
        )
        return self._session_factory

    @property
    def db(self):
        # we are using a scoped_session which always returns the same
        # session if within the same thread
        # https://docs.sqlalchemy.org/en/14/orm/contextual.html
        return self.session_factory()

    @property
    def redis(self):
        if hasattr(self, "_redis"):
            return self._redis
        self._redis = redis.Redis.from_url(self.redis_url)
        return self._redis

    @property
    def configuration(self):
        return orm.CondaStoreConfiguration.configuration(self.db)

    @property
    def storage(self):
        if hasattr(self, "_storage"):
            return self._storage
        self._storage = self.storage_class(parent=self, log=self.log)
        return self._storage

    @property
    def celery_app(self):
        if hasattr(self, "_celery_app"):
            return self._celery_app

        self._celery_app = Celery(
            "tasks",
            backend=self.celery_results_backend,
            broker=self.celery_broker_url,
            include=[
                "conda_store_server.worker.tasks",
            ],
        )
        self._celery_app.conf.beat_schedule = {
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
        }

        return self._celery_app

    def ensure_namespace(self):
        """Ensure that conda-store default namespaces exists"""
        namespace = api.get_namespace(self.db, name=self.default_namespace)
        if namespace is None:
            api.create_namespace(self.db, name=self.default_namespace)

    def ensure_directories(self):
        """Ensure that conda-store filesystem directories exist"""
        os.makedirs(self.store_directory, exist_ok=True)

    def ensure_conda_channels(self):
        """Ensure that conda-store allowed channels and packages are in database"""
        self.log.info("updating conda store channels")

        for channel in self.conda_allowed_channels:
            normalized_channel = conda.normalize_channel_name(
                self.conda_channel_alias, channel
            )

            conda_channel = api.get_conda_channel(self.db, normalized_channel)
            if conda_channel is None:
                conda_channel = orm.CondaChannel(
                    name=normalized_channel, last_update=None
                )
                self.db.add(conda_channel)
                self.db.commit()

    def register_solve(self, specification: schema.CondaSpecification):
        specification_model = self.validate_specification(
            conda_store=self,
            namespace="solve",
            specification=specification,
        )
        specification_sha256 = utils.datastructure_hash(specification_model.dict())
        specification = api.get_specification(self.db, sha256=specification_sha256)
        if specification is None:
            self.log.info(
                f"specification name={specification_model.name} sha256={specification_sha256} registered"
            )
            specification = orm.Specification(specification_model.dict())
            self.db.add(specification)
            self.db.commit()
        else:
            self.log.debug(
                f"specification name={specification_model.name} sha256={specification_sha256} already registered"
            )

        solve_model = orm.Solve(specification_id=specification.id)
        self.db.add(solve_model)
        self.db.commit()

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        task = tasks.task_solve_conda_environment.apply_async(
            args=[solve_model.id], time_limit=self.conda_max_solve_time
        )

        return task, solve_model.id

    def register_environment(
        self, specification: dict, namespace: str = None, force_build=False
    ):
        """Register a given specification to conda store with given namespace/name.

        If force_build is True a build will be triggered even if
        specification already exists.

        """
        namespace = namespace or self.default_namespace

        # Create Namespace if namespace if it does not exist
        namespace_model = api.get_namespace(self.db, name=namespace)
        if namespace_model is None:
            namespace = api.create_namespace(self.db, name=namespace)
            self.db.commit()
        else:
            namespace = namespace_model

        specification_model = self.validate_specification(
            conda_store=self,
            namespace=namespace.name,
            specification=schema.CondaSpecification.parse_obj(specification),
        )
        specification_sha256 = utils.datastructure_hash(specification_model.dict())

        specification = api.get_specification(self.db, sha256=specification_sha256)
        if specification is None:
            self.log.info(
                f"specification name={specification_model.name} sha256={specification_sha256} registered"
            )
            specification = orm.Specification(specification_model.dict())
            self.db.add(specification)
            self.db.commit()
        else:
            self.log.debug(
                f"specification name={specification_model.name} sha256={specification_sha256} already registered"
            )
            if not force_build:
                return

        # Create Environment if specification of given namespace/name
        # does not exist yet
        environment = api.get_environment(
            self.db, namespace_id=namespace.id, name=specification.name
        )
        environment_was_empty = environment is None
        if environment_was_empty:
            environment = orm.Environment(
                name=specification.name,
                namespace_id=namespace.id,
            )
            self.db.add(environment)
            self.db.commit()

        build = self.create_build(environment.id, specification.sha256)

        if environment_was_empty:
            environment.current_build = build
            self.db.commit()

        return build.id

    def create_build(self, environment_id: int, specification_sha256: str):
        specification = api.get_specification(self.db, specification_sha256)
        build = orm.Build(
            environment_id=environment_id, specification_id=specification.id
        )
        self.db.add(build)
        self.db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        artifact_tasks = []
        if schema.BuildArtifactType.YAML in self.build_artifacts:
            artifact_tasks.append(tasks.task_build_conda_env_export.si(build.id))
        if schema.BuildArtifactType.CONDA_PACK in self.build_artifacts:
            artifact_tasks.append(tasks.task_build_conda_pack.si(build.id))
        if schema.BuildArtifactType.DOCKER_MANIFEST in self.build_artifacts:
            artifact_tasks.append(tasks.task_build_conda_docker.si(build.id))

        (
            tasks.task_update_storage_metrics.si()
            | tasks.task_build_conda_environment.si(build.id)
            | group(*artifact_tasks)
            | tasks.task_update_storage_metrics.si()
        ).apply_async()

        return build

    def update_environment_build(self, namespace, name, build_id):
        build = api.get_build(self.db, build_id)
        if build is None:
            raise utils.CondaStoreError(f"build id={build_id} does not exist")

        environment = api.get_environment(self.db, namespace=namespace, name=name)
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
        self.db.commit()

        self.celery_app
        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        tasks.task_update_environment_build.si(environment.id).apply_async()

    def delete_namespace(self, namespace):
        namespace = api.get_namespace(self.db, name=namespace)
        if namespace is None:
            raise utils.CondaStoreError(f"namespace={namespace} does not exist")

        utcnow = datetime.datetime.utcnow()
        namespace.deleted_on = utcnow
        for environment_orm in namespace.environments:
            environment_orm.deleted_on = utcnow
            for build in environment_orm.builds:
                build.deleted_on = utcnow
        self.db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        tasks.task_delete_namespace.si(namespace.id).apply_async()

    def delete_environment(self, namespace, name):
        environment = api.get_environment(self.db, namespace=namespace, name=name)
        if environment is None:
            raise utils.CondaStoreError(
                f"environment namespace={namespace} name={name} does not exist"
            )

        utcnow = datetime.datetime.utcnow()
        environment.deleted_on = utcnow
        for build in environment.builds:
            build.deleted_on = utcnow
        self.db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        tasks.task_delete_environment.si(environment.id).apply_async()

    def delete_build(self, build_id):
        build = api.get_build(self.db, build_id)
        if build.status not in [
            schema.BuildStatus.FAILED,
            schema.BuildStatus.COMPLETED,
        ]:
            raise utils.CondaStoreError(
                "cannot delete build since not finished building"
            )

        build.deleted_on = datetime.datetime.utcnow()
        self.db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        tasks.task_delete_build.si(build.id).apply_async()
