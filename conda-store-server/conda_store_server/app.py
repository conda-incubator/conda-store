import os
import pathlib
import datetime
import shutil

import yaml
from traitlets import Type, Unicode, Integer
from traitlets.config import LoggingConfigurable
from sqlalchemy.engine.url import URL

from conda_store_server import orm, utils, storage, schema


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

    database_raw_url = Unicode(
        None,
        help="RFC-1738 compliant url for the database. e.g. 'sqlite:///conda-store.sqlite';"
        " see https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls for"
        " more information. to avoid handling character escape yourself, consider using"
        " the individual `database_*` settings.",
        config=True,
        allow_none=True,
    )

    database_backend = Unicode(
        "sqlite",
        help="backend (+ driver) sqlalchemy will use. e.g. 'sqlite' or 'postgresql+psycopg2'",
        config=True,
    )

    database_username = Unicode(
        None,
        help="login name for the database. e.g. 'admin'",
        config=True,
        allow_none=True,
    )

    database_password = Unicode(
        None,
        help="password to log in the database. e.g. 'p4ssw0rd'",
        config=True,
        allow_none=True,
    )

    database_host = Unicode(
        None,
        help="server address where the database is running. e.g. 'localhost'",
        config=True,
        allow_none=True,
    )

    database_port = Integer(
        None,
        help="port where the database accepts connections. e.g. '5432'",
        config=True,
        allow_none=True,
    )

    database_path = Unicode(
        "conda-store.sqlite",
        help="path in the server where the database is located. e.g. 'conda-store.sqlite'",
        config=True,
        allow_none=True,
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

    @property
    def database_url(self):
        if self.database_raw_url:
            return self.database_raw_url

        return URL.create(
            self.database_backend,
            self.database_username,
            self.database_password,
            self.database_host,
            self.database_port,
            self.database_path,
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

    def ensure_directories(self):
        os.makedirs(self.store_directory, exist_ok=True)
        os.makedirs(self.environment_directory, exist_ok=True)

    def update_storage_metrics(self):
        configuration = self.configuration
        disk_usage = shutil.disk_usage(str(self.store_directory))
        configuration.disk_usage = disk_usage.used
        configuration.free_storage = disk_usage.free
        configuration.total_storage = disk_usage.total
        self.db.commit()
        return disk_usage

    def update_conda_channels(self, channels=None, update_interval=60 * 60):
        channels = channels or {
            "https://repo.anaconda.com/pkgs/main",
            "https://conda.anaconda.org/conda-forge",
        }

        configuration = self.configuration
        if (configuration.last_package_update is not None) and (
            configuration.last_package_update
            + datetime.timedelta(seconds=update_interval)
            < datetime.datetime.now()
        ):
            self.log.info(
                f"packages were updated in the last seconds={update_interval}"
            )
            return

        for channel in channels:
            orm.CondaPackage.add_channel_packages(self.db, channel)

        configuration.last_package_update = datetime.datetime.utcnow()
        self.db.commit()

    def register_environment(self, specification, namespace="library"):
        if isinstance(specification, (str, pathlib.Path)):
            with open(str(specification)) as f:
                specification = yaml.safe_load(f)

        specification = schema.CondaSpecification.parse_obj(specification)

        # Create Environment Placeholder if does not exist
        query = self.db.query(orm.Environment).filter(
            orm.Environment.name == specification.name
        )
        if query.count() == 0:
            self.db.add(orm.Environment(name=specification.name, namespace=namespace))
        self.db.commit()

        specification_sha256 = utils.datastructure_hash(specification.dict())
        query = self.db.query(orm.Specification).filter(
            orm.Specification.sha256 == specification_sha256
        )
        if query.count() != 0:
            self.log.debug(
                f"already registered specification name={specification.name} sha256={specification_sha256}"
            )
            return

        self.log.info(
            f"registering specification name={specification.name} sha256={specification_sha256}"
        )
        specification = orm.Specification(specification.dict())
        self.db.add(specification)
        self.db.commit()
        self.log.info(
            f"scheduling specification for build name={specification.name} sha256={specification.sha256}"
        )
        build = orm.Build(specification_id=specification.id)
        self.db.add(build)
        self.db.commit()
