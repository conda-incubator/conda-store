import os

from celery import Celery
from traitlets import Type, Unicode, Integer, List, default
from traitlets.config import LoggingConfigurable

from conda_store_server import orm, utils, storage, schema, api, conda


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

    environment_directory = Unicode(
        "conda-store-state/envs",
        help="directory for symlinking conda environment builds",
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

    conda_allowed_channels = List(
        ["https://repo.anaconda.com/pkgs/main", "conda-forge"],
        help="Allowed conda channels to be used in conda environments. Currently not enforced",
        config=True,
    )

    database_url = Unicode(
        "sqlite:///conda-store.sqlite",
        help="url for the database. e.g. 'sqlite:///conda-store.sqlite'",
        config=True,
    )

    celery_broker_url = Unicode(
        help="broker url to use for celery tasks",
        config=True,
    )

    @default("celery_broker_url")
    def _default_celery_broker_url(self):
        return f"sqla+{self.database_url}"

    celery_results_backend = Unicode(
        help="backend to use for celery task results",
        config=True,
    )

    @default("celery_results_backend")
    def _default_celery_results_backend(self):
        return f"db+{self.database_url}"

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
        "frolvlad/alpine-glibc:latest",
        help="default base image used for the Dockerized environments",
        config=True,
    )

    @property
    def session_factory(self):
        if hasattr(self, "_session_factory"):
            return self._session_factory

        self._session_factory = orm.new_session_factory(url=self.database_url)
        return self._session_factory

    @property
    def db(self):
        if hasattr(self, "_db"):
            return self._db
        self._db = self.session_factory()
        return self._db

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

        if self.celery_results_backend.startswith("sqla"):
            # https://github.com/celery/celery/issues/4653#issuecomment-400029147
            # race condition in table construction in celery
            # despite issue being closed still causes first task to fail
            # in celery if tables not created
            from celery.backends.database import SessionManager

            session = SessionManager()
            engine = session.get_engine(self._celery_app.backend.url)
            session.prepare_models(engine)

        return self._celery_app

    def ensure_directories(self):
        """Ensure that conda-store filesystem directories exist"""
        os.makedirs(self.store_directory, exist_ok=True)
        os.makedirs(self.environment_directory, exist_ok=True)

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

        for channel in api.list_conda_channels(self.db):
            channel.update_packages(self.db)

    def register_environment(
        self, specification: dict, namespace: str = "default", force_build=False
    ):
        """Register a given specification to conda store with given namespace/name.

        If force_build is True a build will be triggered even if
        specification already exists.

        """
        specification_model = schema.CondaSpecification.parse_obj(specification)
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

        build = self.create_build(specification.sha256)

        # Create Environment if specification of given namespace/name
        # does not exist yet
        environment = api.get_environment(
            self.db, namespace=namespace, name=specification.name
        )
        if environment is None:
            self.db.add(
                orm.Environment(
                    name=specification.name,
                    namespace=namespace,
                    specification_id=specification.id,
                    build_id=build.id,
                )
            )
            self.db.commit()

    def create_build(self, specification_sha256):
        specification = api.get_specification(self.db, specification_sha256)
        build = orm.Build(specification_id=specification.id)
        self.db.add(build)
        self.db.commit()

        self.celery_app

        # must import tasks after a celery app has been initialized
        from conda_store_server.worker import tasks

        (
            tasks.task_update_storage_metrics.si()
            | tasks.task_build_conda_environment.si(build.id)
            | tasks.task_build_conda_pack.si(build.id)
            | tasks.task_build_conda_docker.si(build.id)
            | tasks.task_update_storage_metrics.si()
        ).apply_async()

        return build
