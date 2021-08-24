import os
import enum
import datetime
import shutil

from sqlalchemy import (
    Table,
    Column,
    BigInteger,
    Integer,
    String,
    JSON,
    Enum,
    DateTime,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import create_engine

from conda_store_server import utils
from conda_store_server.environment import validate_environment
from conda_store_server.conda import download_repodata


Base = declarative_base()


class BuildArtifactType(enum.Enum):
    DIRECTORY = "DIRECTORY"
    LOCKFILE = "LOCKFILE"
    LOGS = "LOGS"
    YAML = "YAML"
    CONDA_PACK = "CONDA_PACK"
    DOCKER_BLOB = "DOCKER_BLOB"
    DOCKER_MANIFEST = "DOCKER_MANIFEST"


class BuildStatus(enum.Enum):
    QUEUED = "QUEUED"
    BUILDING = "BUILDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Namespace(Base):
    """Namespace for resources"""

    __tablename__ = "namespace"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Specification(Base):
    """The specifiction for a given conda environment"""

    __tablename__ = "specification"

    def __init__(self, specification):
        if not validate_environment(specification):
            raise ValueError(
                "specification={specification} is not valid conda environment.yaml"
            )
        self.name = specification["name"]
        self.spec = specification
        self.sha256 = utils.datastructure_hash(self.spec)

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    spec = Column(JSON, nullable=False)
    sha256 = Column(String, unique=True, nullable=False)
    created_on = Column(DateTime, default=datetime.datetime.utcnow)

    builds = relationship("Build", back_populates="specification")


build_conda_package = Table(
    "build_conda_package",
    Base.metadata,
    Column("build_id", ForeignKey("build.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "conda_package_id",
        ForeignKey("conda_package.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Build(Base):
    """The state of a build of a given specification"""

    __tablename__ = "build"

    id = Column(Integer, primary_key=True)
    specification_id = Column(Integer, ForeignKey("specification.id"), nullable=False)
    specification = relationship(Specification, back_populates="builds")

    namespace_id = Column(Integer, ForeignKey("namespace.id"), nullable=False)
    namespace = relationship(Namespace)

    packages = relationship("CondaPackage", secondary=build_conda_package)

    status = Column(Enum(BuildStatus), default=BuildStatus.QUEUED)
    size = Column(BigInteger, default=0)
    scheduled_on = Column(DateTime, default=datetime.datetime.utcnow)
    started_on = Column(DateTime, default=None)
    ended_on = Column(DateTime, default=None)
    deleted_on = Column(DateTime, default=None)

    build_artifacts = relationship("BuildArtifact", back_populates="build")

    def build_path(self, store_directory):
        store_path = os.path.abspath(store_directory)
        return os.path.join(store_path, self.build_key)

    def environment_path(self, environment_directory):
        environment_directory = os.path.abspath(environment_directory)
        return os.path.join(environment_directory, self.specification.name)

    @property
    def build_key(self):
        """A conda environment build is a function of the sha256 of the
        environment.yaml along with the time that the package was built.

        The last two parts of the build key are to assist finding the
        record in the database.

        The build key should be a key that allows for the environment
        build to be easily identified and found in the database.
        """
        datetime_format = "%Y%m%d-%H%M%S-%f"
        return f"{self.specification.sha256}-{self.scheduled_on.strftime(datetime_format)}-{self.id}-{self.specification.name}"

    @staticmethod
    def parse_build_key(key):
        parts = key.split("-")
        if len(parts) < 5:
            return None
        return int(parts[4])  # build_id

    @property
    def log_key(self):
        return f"logs/{self.build_key}.log"

    @property
    def conda_env_export_key(self):
        return f"yaml/{self.build_key}.yml"

    @property
    def conda_pack_key(self):
        return f"archive/{self.build_key}.tar.gz"

    @property
    def docker_manifest_key(self):
        return f"docker/manifest/{self.build_key}"

    def docker_blob_key(self, blob_hash):
        return f"docker/blobs/{blob_hash}"

    @hybrid_property
    def has_lockfile(self):
        return any(
            artifact.artifact_type == BuildArtifactType.LOCKFILE
            for artifact in self.build_artifacts
        )

    @hybrid_property
    def has_yaml(self):
        return any(
            artifact.artifact_type == BuildArtifactType.YAML
            for artifact in self.build_artifacts
        )

    @hybrid_property
    def has_conda_pack(self):
        return any(
            artifact.artifact_type == BuildArtifactType.CONDA_PACK
            for artifact in self.build_artifacts
        )

    @hybrid_property
    def has_docker_manifest(self):
        return any(
            artifact.artifact_type == BuildArtifactType.DOCKER_MANIFEST
            for artifact in self.build_artifacts
        )


class BuildArtifact(Base):
    """Artifacts of a given build"""

    __tablename__ = "build_artifact"

    id = Column(Integer, primary_key=True)

    build_id = Column(Integer, ForeignKey("build.id"))
    build = relationship(Build, back_populates="build_artifacts")

    artifact_type = Column(Enum(BuildArtifactType), nullable=False)

    key = Column(String)


class Environment(Base):
    """Pointer to the current build and specification for a given
    environment name

    """

    __tablename__ = "environment"

    __table_args__ = (
        UniqueConstraint("namespace_id", "name", name="_namespace_name_uc"),
    )

    id = Column(Integer, primary_key=True)

    namespace_id = Column(Integer, ForeignKey("namespace.id"), nullable=False)
    namespace = relationship(Namespace)

    name = Column(String, nullable=False)

    build_id = Column(Integer, ForeignKey("build.id"))
    build = relationship(Build)


class CondaChannel(Base):
    __tablename__ = "conda_channel"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    last_update = Column(DateTime)

    def update_packages(self, db):
        repodata = download_repodata(self.name, self.last_update)
        if not repodata:
            # nothing to update
            return

        for architecture in repodata:
            packages = list(repodata[architecture]["packages"].values())

            existing_architecture_sha256 = {
                _[0]
                for _ in db.query(CondaPackage.sha256)
                .filter(CondaPackage.channel_id == self.id)
                .filter(CondaPackage.subdir == architecture)
                .all()
            }
            for package in packages:
                if package["sha256"] not in existing_architecture_sha256:
                    db.add(
                        CondaPackage(
                            build=package["build"],
                            build_number=package["build_number"],
                            constrains=package.get("constrains"),
                            depends=package["depends"],
                            license=package.get("license"),
                            license_family=package.get("liciense_family"),
                            md5=package["md5"],
                            sha256=package["sha256"],
                            name=package["name"],
                            size=package["size"],
                            subdir=package.get("subdir"),
                            timestamp=package.get("timestamp"),
                            version=package["version"],
                            channel_id=self.id,
                        )
                    )
                    existing_architecture_sha256.add(package["sha256"])
            db.commit()

        self.last_update = datetime.datetime.utcnow()
        db.commit()


class CondaPackage(Base):
    __tablename__ = "conda_package"

    __table_args__ = (
        UniqueConstraint(
            "channel_id",
            "subdir",
            "name",
            "version",
            "build",
            "build_number",
            "sha256",
            name="_conda_package_uc",
        ),
    )

    id = Column(Integer, primary_key=True)

    channel_id = Column(Integer, ForeignKey("conda_channel.id"))
    channel = relationship(CondaChannel)

    build = Column(String, nullable=False)
    build_number = Column(Integer, nullable=False)
    constrains = Column(JSON, nullable=True)
    depends = Column(JSON, nullable=False)
    license = Column(String, nullable=True)
    license_family = Column(String, nullable=True)
    md5 = Column(String, nullable=False)
    name = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    size = Column(BigInteger, nullable=False)
    subdir = Column(String, nullable=True)
    timestamp = Column(BigInteger, nullable=True)
    version = Column(String, nullable=False)

    def __repr__(self):
        return f"<CondaPackage (channel={self.channel} name={self.name} version={self.version} sha256={self.sha256})>"


class CondaStoreConfiguration(Base):
    __tablename__ = "conda_store_configuration"

    id = Column(Integer, primary_key=True)

    disk_usage = Column(BigInteger, default=0)
    free_storage = Column(BigInteger, default=0)
    total_storage = Column(BigInteger, default=0)

    @classmethod
    def configuration(cls, db):
        query = db.query(cls).filter(cls.id == 1)
        if query.count() == 0:
            db.add(cls(id=1))
            db.commit()
        return query.first()

    @classmethod
    def update_storage_metrics(cls, db, store_directory):
        configuration = cls.configuration(db)

        disk_usage = shutil.disk_usage(store_directory)
        configuration.disk_usage = disk_usage.used
        configuration.free_storage = disk_usage.free
        configuration.total_storage = disk_usage.total
        db.commit()


def new_session_factory(url="sqlite:///:memory:", reset=False, **kwargs):
    engine = create_engine(url, **kwargs)

    if reset:
        Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)

    session_factory = scoped_session(sessionmaker(bind=engine))
    return session_factory
