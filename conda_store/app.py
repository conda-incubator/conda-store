import pathlib
import datetime
import logging
import shutil

import yaml
from sqlalchemy import and_

from conda_store import orm, utils, storage

logger = logging.getLogger(__name__)


class CondaStore:
    def __init__(self,
                 store_directory,
                 environment_directory=None,
                 database_url=None,
                 storage_backend='s3',
                 default_permissions=None,
                 default_uid=None,
                 default_gid=None):
        self.store_directory = pathlib.Path(store_directory).resolve()
        if not self.store_directory.is_dir():
            logger.info(f'creating directory store_directory={store_directory}')
            self.store_directory.mkdir(parents=True)

        self.environment_directory = pathlib.Path(
            environment_directory or (self.store_directory / 'envs')).resolve()
        if not self.environment_directory.is_dir():
            logger.info(f'creating directory environment_directory={environment_directory}')
            self.environment_directory.mkdir(parents=True)

        self.database_url = database_url or f'sqlite:///{self.store_directory / "conda_store.sqlite"}'

        Session = orm.new_session_factory(url=self.database_url)
        self.db = Session()

        if storage_backend == 'filesystem':
            storage_directory = self.store_directory / 'storage'
            self.storage = storage.LocalStorage(storage_directory)
        elif storage_backend == 's3':
            self.storage = storage.S3Storage()

        self.configuration.store_directory = str(self.store_directory)
        self.configuration.environment_directory = str(self.environment_directory)

        self.update_storage_metrics()
        self.update_conda_channels()

    @property
    def configuration(self):
        return orm.CondaStoreConfiguration.configuration(self.db)

    def update_storage_metrics(self):
        configuration = self.configuration
        disk_usage = shutil.disk_usage(str(self.store_directory))
        configuration.disk_usage = disk_usage.used
        configuration.free_storage = disk_usage.free
        configuration.total_storage = disk_usage.total
        self.db.commit()
        return disk_usage

    def update_conda_channels(self, channels=None, update_interval=60*60):
        channels = channels or {
            'https://repo.anaconda.com/pkgs/main',
            'https://conda.anaconda.org/conda-forge'
        }

        configuration = self.configuration
        if (configuration.last_package_update is not None) and \
           (configuration.last_package_update + datetime.timedelta(seconds=update_interval) < datetime.datetime.now()):
            logger.info(f'packages were updated in the last seconds={update_interval}')
            return

        for channel in channels:
            orm.CondaPackage.add_channel_packages(self.db, channel)

        configuration.last_package_update = datetime.datetime.utcnow()
        self.db.commit()

    def register_environment(self, specification):
        if isinstance(specification, (str, pathlib.Path)):
            with open(str(specification)) as f:
                specification = yaml.safe_load(f)

        # Create Environment Placeholder if does not exist
        query = self.db.query(orm.Environment).filter(
            orm.Environment.name == specification["name"])
        if query.count() == 0:
            self.db.add(orm.Environment(name=specification["name"]))
        self.db.commit()

        specification_sha256 = utils.datastructure_hash(specification)
        query = self.db.query(orm.Specification).filter(
            orm.Specification.sha256 == specification_sha256)
        if query.count() != 0:
            logger.debug(f'already registered specification name={specification["name"]} sha256={specification_sha256}')
            return

        logger.info(f'registering specification name={specification["name"]} sha256={specification_sha256}')
        specification = orm.Specification(specification)
        self.db.add(specification)
        self.db.commit()
        logger.info(f'scheduling specification for build name={specification.name} sha256={specification.sha256}')
        build = orm.Build(specification_id=specification.id)
        self.db.add(build)
        self.db.commit()

    def claim_build(self):
        build = self.db.query(orm.Build).filter(
            orm.Build.status == orm.BuildStatus.QUEUED,
            orm.Build.scheduled_on < datetime.datetime.utcnow()
        ).first()
        build.status = orm.BuildStatus.BUILDING
        build.started_on = datetime.datetime.utcnow()
        self.db.commit()
        return build

    def set_build_failed(self, build, logs):
        self.storage.set(build.log_key, logs, content_type='text/plain')
        build.status = orm.BuildStatus.FAILED
        build.ended_on = datetime.datetime.utcnow()
        self.db.commit()

    def set_build_completed(self, build, logs, packages):
        def package_query(package):
            return self.db.query(orm.CondaPackage).filter(and_(
                orm.CondaPackage.channel == package['base_url'],
                orm.CondaPackage.subdir == package['platform'],
                orm.CondaPackage.name == package['name'],
                orm.CondaPackage.version == package['version'],
                orm.CondaPackage.build == package['build_string'],
                orm.CondaPackage.build_number == package['build_number'],
            ))
        build.packages = [package_query(package).first() for package in packages]
        self.storage.set(build.log_key, logs, content_type='text/plain')
        build.status = orm.BuildStatus.COMPLETED
        build.ended_on = datetime.datetime.utcnow()

        environment = self.db.query(orm.Environment).filter(
            orm.Environment.name == build.specification.name
        ).first()
        environment.build = build
        environment.specification = build.specification
        self.db.commit()
