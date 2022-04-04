import os
import datetime
import shutil
import itertools
import math
from traceback import StackSummary
from unicodedata import name

from sqlalchemy import (
    Table,
    Column,
    BigInteger,
    Integer,
    Unicode,
    Text,
    JSON,
    Enum,
    DateTime,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import sessionmaker, relationship, scoped_session, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import create_engine

from conda_store_server import utils, schema
from conda_store_server.environment import validate_environment
from conda_store_server.conda import download_repodata

#from pdb import set_trace as bp
from celery.contrib.rdb import set_trace as bp

Base = declarative_base()


class Namespace(Base):
    """Namespace for resources"""

    __tablename__ = "namespace"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)

    environments = relationship("Environment", back_populates="namespace")

    deleted_on = Column(DateTime, default=None)


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
    name = Column(Unicode(255), nullable=False)
    spec = Column(JSON, nullable=False)
    sha256 = Column(Unicode(255), unique=True, nullable=False)
    created_on = Column(DateTime, default=datetime.datetime.utcnow)

    builds = relationship("Build", back_populates="specification")


build_conda_package = Table(
    "build_conda_package_build",
    Base.metadata,
    Column("build_id", ForeignKey("build.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "conda_package_build_id",
        ForeignKey("conda_package_build.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Build(Base):
    """The state of a build of a given specification"""

    __tablename__ = "build"

    id = Column(Integer, primary_key=True)
    specification_id = Column(Integer, ForeignKey("specification.id"), nullable=False)
    specification = relationship(Specification, back_populates="builds")

    environment_id = Column(Integer, ForeignKey("environment.id"), nullable=False)
    environment = relationship(
        "Environment",
        backref=backref("builds", cascade="all, delete-orphan"),
        foreign_keys=[environment_id],
    )

    packages = relationship("CondaPackageBuild", secondary=build_conda_package)

    status = Column(Enum(schema.BuildStatus), default=schema.BuildStatus.QUEUED)
    size = Column(BigInteger, default=0)
    scheduled_on = Column(DateTime, default=datetime.datetime.utcnow)
    started_on = Column(DateTime, default=None)
    ended_on = Column(DateTime, default=None)
    deleted_on = Column(DateTime, default=None)

    build_artifacts = relationship(
        "BuildArtifact", back_populates="build", cascade="all, delete-orphan"
    )

    def build_path(self, conda_store):
        """Build path is the directory for the conda prefix used to
        build the environment

        """
        store_directory = os.path.abspath(conda_store.store_directory)
        namespace = self.environment.namespace.name
        name = self.specification.name
        return os.path.join(
            conda_store.build_directory.format(
                store_directory=store_directory, namespace=namespace, name=name
            ),
            self.build_key,
        )

    def environment_path(self, conda_store):
        """Environment path is the path for the symlink to the build
        path

        """
        store_directory = os.path.abspath(conda_store.store_directory)
        namespace = self.environment.namespace.name
        name = self.specification.name
        return os.path.join(
            conda_store.environment_directory.format(
                store_directory=store_directory, namespace=namespace, name=name
            ),
            self.specification.name,
        )

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
            artifact.artifact_type == schema.BuildArtifactType.LOCKFILE
            for artifact in self.build_artifacts
        )

    @hybrid_property
    def has_yaml(self):
        return any(
            artifact.artifact_type == schema.BuildArtifactType.YAML
            for artifact in self.build_artifacts
        )

    @hybrid_property
    def has_conda_pack(self):
        return any(
            artifact.artifact_type == schema.BuildArtifactType.CONDA_PACK
            for artifact in self.build_artifacts
        )

    @hybrid_property
    def has_docker_manifest(self):
        return any(
            artifact.artifact_type == schema.BuildArtifactType.DOCKER_MANIFEST
            for artifact in self.build_artifacts
        )


class BuildArtifact(Base):
    """Artifacts of a given build"""

    __tablename__ = "build_artifact"

    id = Column(Integer, primary_key=True)

    build_id = Column(Integer, ForeignKey("build.id"))
    build = relationship(Build, back_populates="build_artifacts")

    artifact_type = Column(Enum(schema.BuildArtifactType), nullable=False)

    key = Column(Unicode(255))


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

    name = Column(Unicode(255), nullable=False)

    current_build_id = Column(Integer, ForeignKey("build.id"))
    current_build = relationship(
        Build, foreign_keys=[current_build_id], post_update=True
    )

    deleted_on = Column(DateTime, default=None)


class CondaChannel(Base):
    __tablename__ = "conda_channel"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True, nullable=False)
    last_update = Column(DateTime)

    def update_packages(self, db):
        #bp()
        repodata = download_repodata(self.name, self.last_update)
        if not repodata:
            # nothing to update
            return

        for architecture in repodata["architectures"]:
            packages_builds = list(
                repodata["architectures"][architecture]["packages"].values()
            )

            existing_architecture_sha256 = {
                _[0]
                for _ in db.query(CondaPackageBuild.sha256)
                .filter(CondaPackage.channel_id == self.id)
                .filter(CondaPackageBuild.subdir == architecture)
                .all()
            }
            for p_build in packages_builds:
                
                # If the given package build doesn't exist in the DB yet
                if p_build["sha256"] not in existing_architecture_sha256:

                    
                    new_build = CondaPackageBuild(
                                    build=p_build["build"],
                                    build_number=p_build["build_number"],
                                    constrains=p_build.get("constrains"),
                                    depends=p_build["depends"],
                                    md5=p_build["md5"],
                                    sha256=p_build["sha256"],
                                    size=p_build["size"],
                                    subdir=p_build.get("subdir"),
                                    timestamp=p_build.get("timestamp"),
                    )
                    


                    existing_package = db.query(CondaPackage)\
                                        .filter(CondaPackage.name == p_build["name"])\
                                        .filter(CondaPackage.version == p_build["version"])\
                                        .filter(CondaPackage.channel_id == self.id ).all()

                    if len(existing_package) == 0:
                        # the package doesn't exist in DB
                        package = CondaPackage(channel_id=self.id,
                                                license=p_build.get("license"),
                                                license_family=p_build.get("license_family"),
                                                name=p_build["name"],
                                                version=p_build["version"],
                                                summary=repodata.get("packages", {})
                                                        .get(p_build["name"], {})
                                                        .get("summary"),
                                                description=repodata.get("packages", {})
                                                        .get(p_build["name"], {})
                                                        .get("description"),
                        )
                        
                        db.add(package)

                    elif len(existing_package) == 1:
                        # the package exists in DB
                        package = existing_package[0]
                    else:
                        # shouldn't happen, as there's a unique contraint on :
                        # CondaPackage(name, version, channel_id)
                        exception_msg = f"""Multiple packages for the same name, version and channel_id have been found.
                        Name : {p_build["name"]}
                        Version : {p_build["version"]}
                        channel_id : {self.id}
                        """
                        raise Exception(exception_msg)

                    package.builds.append(new_build)
                    db.add(new_build)

                    existing_architecture_sha256.add(p_build["sha256"])
                    db.commit()

            db.commit()

        self.last_update = datetime.datetime.utcnow()
        db.commit()



class CondaPackage(Base):
    __tablename__ = "conda_package"

    __table_args__ = (
        UniqueConstraint(
            "channel_id",
            "name",
            "version",
            name="_conda_package_uc",
        ),
    )

    id = Column(Integer, primary_key=True)

    channel_id = Column(Integer, ForeignKey("conda_channel.id"))
    channel = relationship(CondaChannel)
    
    builds = relationship(
        "CondaPackageBuild", back_populates="package", cascade="all, delete-orphan"
    )

    license = Column(Text, nullable=True)
    license_family = Column(Unicode(64), nullable=True)
    name = Column(Unicode(255), nullable=False)
    version = Column(Unicode(64), nullable=False)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
       return f"<CondaPackage (channel={self.channel} name={self.name} version={self.version})>"


class CondaPackageBuild(Base):
    __tablename__ = "conda_package_build"

    __table_args__ = (
        UniqueConstraint(
            "subdir",
            "build",
            "build_number",
            "sha256",
            name="_conda_package_build_uc",
        ),
    )

    id = Column(Integer, primary_key=True)

    package_id = Column(Integer, ForeignKey("conda_package.id"))
    package = relationship(CondaPackage, back_populates="builds")

    #channel_id = Column(Integer, ForeignKey("conda_channel.id"))
    #channel = relationship(CondaChannel)

    build = Column(Unicode(64), nullable=False)
    build_number = Column(Integer, nullable=False)
    constrains = Column(JSON, nullable=True)
    depends = Column(JSON, nullable=False)
    md5 = Column(Unicode(255), nullable=False)
    sha256 = Column(Unicode(64), nullable=False)
    size = Column(BigInteger, nullable=False)
    subdir = Column(Unicode(64), nullable=True)
    timestamp = Column(BigInteger, nullable=True)
    
    def __repr__(self):
       return f"<CondaPackageBuild (id={self.id} build={self.build} size={self.size} sha256={self.sha256})>"



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
