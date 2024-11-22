# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import datetime
import json
import logging
import os
import pathlib
import shutil
import sys
from functools import partial
from typing import List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Table,
    Text,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    and_,
    create_engine,
    or_,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    backref,
    mapped_column,
    relationship,
    sessionmaker,
    validates,
)

from conda_store_server._internal import conda_utils, schema, utils
from conda_store_server._internal.environment import validate_environment

logger = logging.getLogger("orm")


class Base(DeclarativeBase):
    pass


class Worker(Base):
    """For communicating with the worker process"""

    __tablename__ = "worker"

    id: Mapped[int] = mapped_column(primary_key=True)

    # For checking whether the worker is initialized
    initialized: Mapped[bool] = mapped_column(Boolean, default=False)


class Namespace(Base):
    """Namespace for resources"""

    __tablename__ = "namespace"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(Unicode(255), unique=True)

    environments: Mapped[List["Environment"]] = relationship(back_populates="namespace")

    deleted_on: Mapped[datetime.datetime] = mapped_column(DateTime, default=None)

    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    role_mappings: Mapped[List["NamespaceRoleMapping"]] = relationship(
        "NamespaceRoleMapping", back_populates="namespace"
    )


class NamespaceRoleMapping(Base):
    """Mapping between roles and namespaces"""

    __tablename__ = "namespace_role_mapping"

    id: Mapped[int] = mapped_column(primary_key=True)
    namespace_id: Mapped[int] = mapped_column(
        ForeignKey("namespace.id"), nullable=False
    )
    namespace: Mapped["Namespace"] = relationship(back_populates="role_mappings")

    # arn e.g. <namespace>/<name> like `quansight-*/*` or `quansight-devops/*`
    # The entity must match with ARN_ALLOWED defined in schema.py
    entity: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    # e.g. viewer
    role: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    @validates("entity")
    def validate_entity(self, key, entity):
        if not schema.ARN_ALLOWED_REGEX.match(entity):
            raise ValueError(f"invalid entity={entity}")

        return entity

    @validates("role")
    def validate_role(self, key, role):
        if role == "editor":
            role = "developer"  # alias
        if role not in ["admin", "viewer", "developer"]:
            raise ValueError(f"invalid entity={role}")

        return role


class NamespaceRoleMappingV2(Base):
    """Mapping between roles and namespaces"""

    __tablename__ = "namespace_role_mapping_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Provides access to this namespace
    namespace_id: Mapped[int] = mapped_column(
        ForeignKey("namespace.id"), nullable=False
    )
    namespace: Mapped["Namespace"] = relationship(foreign_keys=[namespace_id])

    # ... for other namespace
    other_namespace_id: Mapped[int] = mapped_column(
        ForeignKey("namespace.id"), nullable=False
    )
    other_namespace: Mapped["Namespace"] = relationship(
        foreign_keys=[other_namespace_id]
    )

    # ... with this role, like 'viewer'
    role: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    @validates("role")
    def validate_role(self, key, role):
        if role == "editor":
            role = "developer"  # alias
        if role not in ["admin", "viewer", "developer"]:
            raise ValueError(f"invalid role={role}")
        return role

    __table_args__ = (
        # Ensures no duplicates can be added with this combination of fields.
        # Note: this doesn't add role because role needs to be unique for each
        # pair of ids.
        UniqueConstraint("namespace_id", "other_namespace_id", name="_uc"),
    )


class Specification(Base):
    """The specifiction for a given conda environment"""

    __tablename__ = "specification"

    def __init__(self, specification, is_lockfile: bool = False):
        if not is_lockfile and not validate_environment(specification):
            raise ValueError(
                "specification={specification} is not valid conda environment.yaml"
            )
        self.name = specification["name"]
        self.spec = specification
        self.sha256 = utils.datastructure_hash(self.spec)
        self.is_lockfile = is_lockfile

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    spec: Mapped[dict] = mapped_column(JSON, nullable=False)
    sha256: Mapped[str] = mapped_column(Unicode(255), unique=True, nullable=False)
    created_on: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    is_lockfile: Mapped[bool]

    builds: Mapped[List["Build"]] = relationship(back_populates="specification")
    solves: Mapped[List["Solve"]] = relationship(back_populates="specification")


solve_conda_package_build = Table(
    "solve_conda_package_build",
    Base.metadata,
    Column("solve_id", ForeignKey("solve.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "conda_package_build_id",
        ForeignKey("conda_package_build.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Solve(Base):
    """A solve for a particular specification"""

    __tablename__ = "solve"

    id: Mapped[int] = mapped_column(primary_key=True)
    specification_id: Mapped[str] = mapped_column(
        ForeignKey("specification.id"), nullable=False
    )
    specification: Mapped["Specification"] = relationship(back_populates="solves")

    scheduled_on: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    started_on: Mapped[datetime.datetime] = mapped_column(DateTime, default=None)
    ended_on: Mapped[datetime.datetime] = mapped_column(DateTime, default=None)

    package_builds: Mapped[List["CondaPackageBuild"]] = relationship(
        secondary=solve_conda_package_build
    )


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

    id: Mapped[int] = mapped_column(primary_key=True)
    specification_id: Mapped[int] = mapped_column(
        ForeignKey("specification.id"), nullable=False
    )
    specification: Mapped["Specification"] = relationship(back_populates="builds")

    environment_id: Mapped[int] = mapped_column(
        ForeignKey("environment.id"), nullable=False
    )
    environment: Mapped["Environment"] = relationship(
        backref=backref("builds", cascade="all, delete-orphan"),
        foreign_keys=[environment_id],
    )

    package_builds: Mapped[List["CondaPackageBuild"]] = relationship(
        secondary=build_conda_package
    )

    status: Mapped[schema.BuildStatus] = mapped_column(
        default=schema.BuildStatus.QUEUED
    )
    # Additional status info that will be provided to the user. DO NOT put
    # sensitive data here
    status_info: Mapped[str] = mapped_column(UnicodeText, default=None)
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    scheduled_on: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    started_on: Mapped[datetime.datetime] = mapped_column(DateTime, default=None)
    ended_on: Mapped[datetime.datetime] = mapped_column(DateTime, default=None)
    deleted_on: Mapped[datetime.datetime] = mapped_column(DateTime, default=None)

    # Only used by build_key_version 3, not necessary for earlier versions
    hash: Mapped[str] = mapped_column(Unicode(32), default=None)

    @staticmethod
    def _get_build_key_version():
        # Uses local import to make sure BuildKey is initialized
        from conda_store_server import BuildKey

        return BuildKey.current_version()

    build_key_version: Mapped[int] = mapped_column(
        default=_get_build_key_version, nullable=False
    )

    @validates("build_key_version")
    def validate_build_key_version(self, key, build_key_version):
        # Uses local import to make sure BuildKey is initialized
        from conda_store_server import BuildKey

        return BuildKey.set_current_version(build_key_version)

    build_artifacts: Mapped[List["BuildArtifact"]] = relationship(
        back_populates="build", cascade="all, delete-orphan"
    )

    def build_path(self, conda_store):
        """Build path is the directory for the conda prefix used to
        build the environment

        """
        # Uses local import to make sure BuildKey is initialized
        from conda_store_server import BuildKey

        if BuildKey.current_version() < 3:
            namespace = self.environment.namespace.name
        else:
            namespace = ""

        store_directory = os.path.abspath(conda_store.store_directory)
        res = (
            pathlib.Path(
                conda_store.build_directory.format(
                    store_directory=store_directory,
                    namespace=namespace,
                )
            )
            / self.build_key
        )
        # conda prefix must be less or equal to 255 chars
        # https://github.com/conda-incubator/conda-store/issues/649
        if len(str(res)) > 255:
            raise utils.BuildPathError("build_path too long: must be <= 255 characters")
        # Note: cannot use the '/' operator to prepend the extended-length
        # prefix
        if sys.platform == "win32" and conda_store.win_extended_length_prefix:
            return pathlib.Path(f"\\\\?\\{res}")
        else:
            return res

    def environment_path(self, conda_store):
        """Environment path is the path for the symlink to the build
        path

        """
        # Uses local import to make sure BuildKey is initialized
        from conda_store_server import BuildKey

        # This is not used with v3 because the whole point of v3 is to avoid any
        # dependence on user-provided variable-size data on the filesystem and
        # by default the environment path contains the namespace and the
        # environment name, which can be arbitrary large. By setting this to
        # None, we're making it clear that this shouldn't be used by other
        # functions, such as when creating symlinks
        if BuildKey.current_version() >= 3:
            return None

        store_directory = os.path.abspath(conda_store.store_directory)
        namespace = self.environment.namespace.name
        name = self.specification.name
        res = pathlib.Path(
            conda_store.environment_directory.format(
                store_directory=store_directory, namespace=namespace, name=name
            )
        )
        # Note: cannot use the '/' operator to prepend the extended-length
        # prefix
        if sys.platform == "win32" and conda_store.win_extended_length_prefix:
            return pathlib.Path(f"\\\\?\\{res}")
        else:
            return res

    @property
    def build_key(self):
        """A conda environment build is a function of the sha256 of the
        environment.yaml along with the time that the package was built.

        The last two parts of the build key are to assist finding the
        record in the database.

        The build key should be a key that allows for the environment
        build to be easily identified and found in the database.
        """
        # Uses local import to make sure BuildKey is initialized
        from conda_store_server import BuildKey

        return BuildKey.get_build_key(self)

    @staticmethod
    def parse_build_key(conda_store: "CondaStore", key: str):  # noqa: F821
        # Uses local import to make sure BuildKey is initialized
        from conda_store_server import BuildKey

        return BuildKey.parse_build_key(conda_store, key)

    @property
    def log_key(self):
        return f"logs/{self.build_key}.log"

    @property
    def conda_lock_key(self):
        return f"lockfile/{self.build_key}.yml"

    @property
    def conda_env_export_key(self):
        return f"yaml/{self.build_key}.yml"

    @property
    def conda_pack_key(self):
        return f"archive/{self.build_key}.tar.gz"

    @property
    def docker_manifest_key(self):
        return f"docker/manifest/{self.build_key}"

    @property
    def constructor_installer_key(self):
        ext = "exe" if sys.platform == "win32" else "sh"
        return f"installer/{self.build_key}.{ext}"

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

    @hybrid_property
    def has_constructor_installer(self):
        return any(
            artifact.artifact_type == schema.BuildArtifactType.CONSTRUCTOR_INSTALLER
            for artifact in self.build_artifacts
        )

    def __repr__(self):
        return f"<Build (id={self.id} status={self.status} nbr package_builds={len(self.package_builds)})>"


class BuildArtifact(Base):
    """Artifacts of a given build"""

    __tablename__ = "build_artifact"

    id: Mapped[int] = mapped_column(primary_key=True)

    build_id: Mapped[int] = mapped_column(ForeignKey("build.id"))

    build: Mapped["Build"] = relationship(back_populates="build_artifacts")

    artifact_type: Mapped[schema.BuildArtifactType]

    key: Mapped[str] = mapped_column(Unicode(255))


class Environment(Base):
    """Pointer to the current build and specification for a given
    environment name

    """

    __tablename__ = "environment"

    __table_args__ = (
        UniqueConstraint("namespace_id", "name", name="_namespace_name_uc"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    namespace_id: Mapped[int] = mapped_column(
        ForeignKey("namespace.id"), nullable=False
    )
    namespace: Mapped["Namespace"] = relationship(Namespace)

    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    current_build_id: Mapped[int] = mapped_column(ForeignKey("build.id"))
    current_build: Mapped["Build"] = relationship(
        foreign_keys=[current_build_id], post_update=True
    )

    deleted_on: Mapped[datetime.datetime] = mapped_column(DateTime, default=None)

    description: Mapped[str] = mapped_column(UnicodeText, default=None)


class CondaChannel(Base):
    __tablename__ = "conda_channel"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(255), unique=True, nullable=False)
    last_update: Mapped[datetime.datetime] = mapped_column(DateTime)

    def update_packages(self, db, subdirs=None):
        logger.info(f"update packages {self.name} ")

        logger.info("Downloading repodata ...  ")
        repodata = conda_utils.download_repodata(
            self.name, self.last_update, subdirs=subdirs
        )
        logger.info("repodata downloaded ")

        # Hint : you can store the file locally for later debug
        # with open(f"~/{self.name.split('/')[-1]}_{datetime.datetime.now()}.json", "w") as f:
        #    f.write(json.dumps(repodata, indent=4, sort_keys=True))

        if not repodata:
            # nothing to update
            return

        for architecture in repodata["architectures"]:
            logger.info(f"architecture  : {architecture} ")

            """
            Context :
               For each architecture, we need to add all the packages (`conda_package`),
               and all their builds (`conda_package_build`), with their relationship.
               As of May 2022, based on the default channels `main` and `conda-forge`,
               there are 136K packages and 367K conda_package_build

            Trick :
               To insert these data fast, we need to get rid of the overhead induced
               by the ORM layer, and use session.bulk_insert_mappings.

            Caveat :
               bulk insertion is handy, but we need to avoid breaking integrity constraint,
               This implies that we need to bulk_insert only new data, filtering out
               the data already in the DB

            Algorithm :
               First step :  we insert all the new conda_package rows
               Second step : we insert all the new conda_package_builds rows

               These steps are detailled below.
            """

            # package_data contains all the data for the iterated architecture.
            # Each dict represents a conda_package_build and also contains
            # thge data of the conda_package
            packages_data = list(
                repodata["architectures"][architecture]["packages"].values()
            )

            # First, we retrieve all the pairs "package name - pacakge version"
            # in the DB. This represents all the existing packages.
            existing_packages_keys = [
                f"{_[0]}-{_[1]}-{self.id}"
                for _ in db.query(CondaPackage.name, CondaPackage.version)
                .filter(CondaPackage.channel_id == self.id)
                .all()
            ]

            # Then, we filter packages_data to keep only the new packages.

            # `packages` associates a key representing the package like "{name}-{version}-{channel_id}"
            # to a dict representing a new package to insert.
            # By using a dict with such key, we avoid potential duplicates from within the repodata.
            packages = {}

            for p_build in packages_data:
                package_key = f'{p_build["name"]}-{p_build["version"]}-{self.id}'

                # Filtering out : if the key already exists in existing_packages_keys,
                # then the package is already if DB, we don't add it.
                if (
                    package_key not in packages
                    and package_key not in existing_packages_keys
                ):
                    new_package_dict = {
                        "channel_id": self.id,
                        "license": p_build.get("license"),
                        "license_family": p_build.get("license_family"),
                        "name": p_build["name"],
                        "version": p_build["version"],
                        "summary": repodata.get("packages", {})
                        .get(p_build["name"], {})
                        .get("summary"),
                        "description": repodata.get("packages", {})
                        .get(p_build["name"], {})
                        .get("description"),
                    }

                    packages[package_key] = new_package_dict

            logger.info(f"packages to insert : {len(packages)} ")

            try:
                db.bulk_insert_mappings(CondaPackage, packages.values())
                db.commit()
            except Exception as e:
                print(f"{e}")
                db.rollback()
                raise e

            logger.info("insert packages done")

            logger.info("retrieving existing sha256  : ")
            existing_sha256 = {
                _[0]
                for _ in db.query(CondaPackageBuild.sha256)
                .join(CondaPackageBuild.package)
                .filter(CondaPackage.channel_id == self.id)
                .filter(CondaPackageBuild.subdir == architecture)
                .all()
            }
            logger.info("retrieved existing sha256  : ")
            logger.info(f"package data before filtering  : {len(packages_data)} ")

            # We store the package builds in a dict indexed by their sha256
            # Later, we keep only the values.
            # That way, any duplicated sha256 from the repodata is erased
            # Also, we exclude pacakge_builds for which the sha256 is already in the DB
            packages_builds = {}
            for pb in packages_data:
                if pb["sha256"] not in existing_sha256:
                    packages_builds[pb["sha256"]] = pb

            packages_builds = packages_builds.values()
            logger.info(f"package builds after filtering : {len(packages_builds)} ")

            # This associates a tuple like "(name,version)" representing a package
            # to all its builds
            package_builds = {}
            logger.info("Creating CondaPackageBuild objects")
            for p_build in packages_builds:
                has_null = False
                non_null_keys = [
                    "build",
                    "build_number",
                    "depends",
                    "md5",
                    "sha256",
                    "size",
                ]
                for k in non_null_keys:
                    if p_build[k] is None:
                        has_null = True
                        break
                if has_null:
                    continue

                if p_build["depends"] == []:
                    p_build["depends"] = ""

                package_key = (p_build["name"], p_build["version"])

                new_package_build_dict = {
                    "build": p_build["build"],
                    "build_number": p_build["build_number"],
                    "channel_id": self.id,
                    "constrains": p_build.get("constrains"),
                    "depends": p_build["depends"],
                    "md5": p_build["md5"],
                    "sha256": p_build["sha256"],
                    "size": p_build["size"],
                    "subdir": p_build.get("subdir"),
                    "timestamp": p_build.get("timestamp"),
                }

                if package_key not in package_builds:
                    package_builds[package_key] = []

                package_builds[package_key].append(new_package_build_dict)
            logger.info("CondaPackageBuild objects created")

            # sqlite3 has a max expression depth of 1000
            batch_size = 990
            all_package_keys = list(package_builds.keys())
            for i in range(0, len(all_package_keys), batch_size):
                logger.info(f"handling subset at index {i} (batch size {batch_size})")
                subset_keys = all_package_keys[i : i + batch_size]

                # retrieve the parent packages for the subset
                logger.info("retrieve the parent packages for the subset ")
                statements = []
                for p_name, p_version in subset_keys:
                    statements.append(
                        and_(
                            CondaPackage.name == p_name,
                            CondaPackage.version == p_version,
                            CondaPackage.channel_id == self.id,
                        )
                    )
                all_parent_packages = (
                    db.query(CondaPackage).filter(or_(*statements)).all()
                )
                all_parent_packages = {
                    (_.name, _.version): _ for _ in all_parent_packages
                }
                logger.info(f"parent packages retrieved : {len(all_parent_packages)} ")

                for p_name, p_version in subset_keys:
                    for p_build_dict in package_builds[(p_name, p_version)]:
                        p_build_dict["package_id"] = all_parent_packages[
                            (p_name, p_version)
                        ].id

                logger.info("ready to bulk save")

            try:
                flatten = []
                for p_name, p_version in package_builds:
                    flatten += package_builds[(p_name, p_version)]

                db.bulk_insert_mappings(CondaPackageBuild, flatten)
                db.commit()
                logger.info("bulk saved")
            except Exception as e:
                logger.error(f"{e}")

                raise e

            logger.info(f"DONE for architecture  : {architecture}")

        self.last_update = datetime.datetime.utcnow()
        db.commit()
        logger.info("update packages DONE ")


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

    id: Mapped[int] = mapped_column(primary_key=True)

    channel_id: Mapped[int] = mapped_column(ForeignKey("conda_channel.id"), index=True)
    channel: Mapped["CondaChannel"] = relationship(CondaChannel)

    builds: Mapped[List["CondaPackageBuild"]] = relationship(
        back_populates="package", cascade="all, delete-orphan"
    )

    license: Mapped[str] = mapped_column(Text, nullable=True)
    license_family: Mapped[str] = mapped_column(Unicode(64), nullable=True)
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(Unicode(64), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<CondaPackage (channel={self.channel_id} name={self.name} version={self.version})>"


class CondaPackageBuild(Base):
    __tablename__ = "conda_package_build"

    __table_args__ = (
        UniqueConstraint(
            "channel_id",
            "package_id",
            "subdir",
            "build",
            "build_number",
            "sha256",
            name="_conda_package_build_uc",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    package_id: Mapped[int] = mapped_column(ForeignKey("conda_package.id"))
    package: Mapped["CondaPackage"] = relationship(back_populates="builds")

    """
    Some package builds have the exact same data from different channels.
    Thus, when adding a channel, populating CondaPackageBuild can encounter
    duplicate keys errors. That's why we need to distinguish them by channel_id.
    """
    channel_id: Mapped[int] = mapped_column(ForeignKey("conda_channel.id"))
    channel: Mapped["CondaChannel"] = relationship(CondaChannel)

    build: Mapped[int] = mapped_column(Unicode(64), index=True)
    build_number: Mapped[int]
    constrains: Mapped[dict] = mapped_column(JSON)
    depends: Mapped[dict] = mapped_column(JSON)
    md5: Mapped[str] = mapped_column(Unicode(255))
    sha256: Mapped[str] = mapped_column(Unicode(64))
    size: Mapped[int] = mapped_column(BigInteger)
    subdir: Mapped[str] = mapped_column(Unicode(64))
    timestamp: Mapped[int] = mapped_column(BigInteger)

    def __repr__(self):
        return f"<CondaPackageBuild (id={self.id} build={self.build} size={self.size} sha256={self.sha256})>"


class CondaStoreConfiguration(Base):
    __tablename__ = "conda_store_configuration"

    id: Mapped[int] = mapped_column(primary_key=True)

    disk_usage: Mapped[int] = mapped_column(BigInteger, default=0)
    free_storage: Mapped[int] = mapped_column(BigInteger, default=0)
    total_storage: Mapped[int] = mapped_column(BigInteger, default=0)

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


class KeyValueStore(Base):
    """KeyValueStore use to store arbitrary prefix, key, values"""

    __tablename__ = "keyvaluestore"
    __table_args__ = (UniqueConstraint("prefix", "key", name="_prefix_key_uc"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    prefix: Mapped[str] = mapped_column(Unicode)
    key: Mapped[str] = mapped_column(Unicode)
    value: Mapped[dict] = mapped_column(JSON)


def new_session_factory(
    url="sqlite:///:memory:", reset=False, **kwargs
) -> sessionmaker:
    engine = create_engine(
        url,
        # See the comment on the CustomJSONEncoder class on why this is needed
        json_serializer=partial(json.dumps, cls=utils.CustomJSONEncoder),
        **kwargs,
    )

    session_factory = sessionmaker(bind=engine)
    return session_factory
