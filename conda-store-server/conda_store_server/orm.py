import enum
import datetime
import logging
import pathlib

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
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from conda_store_server import utils
from conda_store_server.environment import validate_environment
from conda_store_server.conda import download_repodata, normalize_channel_name


logger = logging.getLogger(__name__)


Base = declarative_base()


class BuildStatus(enum.Enum):
    QUEUED = "QUEUED"
    BUILDING = "BUILDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Specification(Base):
    """The specifiction for a given conda environment

    """

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
    """The state of a build of a given specification

    """

    __tablename__ = "build"

    id = Column(Integer, primary_key=True)
    specification_id = Column(Integer, ForeignKey("specification.id"), nullable=False)
    specification = relationship(Specification, back_populates="builds")

    packages = relationship("CondaPackage", secondary=build_conda_package)

    status = Column(Enum(BuildStatus), default=BuildStatus.QUEUED)
    size = Column(Integer, default=0)
    scheduled_on = Column(DateTime, default=datetime.datetime.utcnow)
    started_on = Column(DateTime, default=None)
    ended_on = Column(DateTime, default=None)

    def build_path(self, store_directory):
        store_path = pathlib.Path(store_directory).resolve()
        return store_path / f"{self.specification.sha256}-{self.specification.name}"

    def environment_path(self, environment_directory):
        environment_directory = pathlib.Path(environment_directory).resolve()
        return environment_directory / self.specification.name

    @property
    def log_key(self):
        return f"logs/{self.specification.name}/{self.specification.sha256}/{self.id}"

    @property
    def conda_pack_key(self):
        return f"archive/{self.specification.name}/{self.specification.sha256}/{self.id}.tar.gz"

    @property
    def docker_manifest_key(self):
        return f"docker/manifest/{self.specification.name}/{self.specification.sha256}"

    def docker_blob_key(self, blob_hash):
        return f"docker/blobs/{blob_hash}"


class Environment(Base):
    """Pointer to the current build and specification for a given
    environment name

    """

    __tablename__ = "environment"

    __table_args__ = (UniqueConstraint("namespace", "name", name="_namespace_name_uc"),)

    id = Column(Integer, primary_key=True)
    namespace = Column(String, default="library")
    name = Column(String, nullable=False)

    specification_id = Column(Integer, ForeignKey("specification.id"))
    specification = relationship(Specification)

    build_id = Column(Integer, ForeignKey("build.id"))
    build = relationship(Build)


class CondaPackage(Base):
    __tablename__ = "conda_package"

    id = Column(Integer, primary_key=True)
    channel = Column(String, nullable=False)
    build = Column(String, nullable=False)
    build_number = Column(Integer, nullable=False)
    constrains = Column(JSON, nullable=True)
    depends = Column(JSON, nullable=False)
    license = Column(String, nullable=True)
    license_family = Column(String, nullable=True)
    md5 = Column(String, nullable=False)
    name = Column(String, nullable=False)
    sha256 = Column(String, unique=True)
    size = Column(BigInteger, nullable=False)
    subdir = Column(String, nullable=True)
    timestamp = Column(BigInteger, nullable=True)
    version = Column(String, nullable=False)

    builds = relationship(Build, secondary=build_conda_package)

    @classmethod
    def add_channel_packages(cls, db, channel):
        channel = normalize_channel_name(channel)
        repodata = download_repodata(channel)
        existing_sha256 = {_[0] for _ in db.query(cls.sha256).all()}

        for architecture in repodata:
            packages = list(repodata[architecture]["packages"].values())
            for package in packages:
                if package["sha256"] not in existing_sha256:
                    db.add(
                        cls(
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
                            channel=channel,
                        )
                    )
        db.commit()

    def __repr__(self):
        return f"<CondaPackage (channel={self.channel} name={self.name} version={self.version} sha256={self.sha256})>"


class CondaStoreConfiguration(Base):
    __tablename__ = "conda_store_configuration"

    id = Column(Integer, primary_key=True)
    store_directory = Column(String)
    environment_directory = Column(String)

    default_permissions = Column(String, default=None)
    default_uid = Column(String, default=None)
    default_gid = Column(String, default=None)

    last_package_update = Column(DateTime)

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


def new_session_factory(url="sqlite:///:memory:", reset=False, **kwargs):
    engine = create_engine(url, **kwargs)

    if reset:
        Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)
    return session_factory
