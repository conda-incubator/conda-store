# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
from __future__ import annotations

import datetime
import hashlib
import typing

import platformdirs

if typing.TYPE_CHECKING:
    from ._internal.orm import Build
    from .app import CondaStore


__version__ = "2024.11.2"


CONDA_STORE_DIR = platformdirs.user_data_path(appname="conda-store")


class BuildKey:
    """
    Used to configure the build key format, which identifies a particular
    environment build

    Avoids a cyclic dependency between the `orm` module and the module defining
    `CondaStore.build_key_version`. Because the `orm` module is loaded early on
    startup, we want to delay initialization of the `Build.build_key_version`
    field until `CondaStore.build_key_version` has been read from the config.

    Because the build key version needs to be the same for the entire
    application, this class implements the singleton pattern. Users are expected
    to use class methods instead of creating class instances. All implementation
    details are hidden within the class, preventing potential issues caused by
    cyclic imports.
    """

    # Default version, must be None here. Initialized in CondaStore.build_key_version
    _current_version = None

    _version2_hash_size = 8

    _version3_experimental_hash_size = 32

    def _version1_fmt(build: Build) -> str:  # noqa: F821
        datetime_format = "%Y%m%d-%H%M%S-%f"
        hash = build.specification.sha256
        timestamp = build.scheduled_on.strftime(datetime_format)
        id = build.id
        name = build.specification.name
        return f"{hash}-{timestamp}-{id}-{name}"

    def _version2_fmt(build: Build) -> str:  # noqa: F821
        tzinfo = datetime.timezone.utc
        hash = build.specification.sha256[: BuildKey._version2_hash_size]
        timestamp = int(build.scheduled_on.replace(tzinfo=tzinfo).timestamp())
        id = build.id
        name = build.specification.name
        return f"{hash}-{timestamp}-{id}-{name}"

    # Warning: this is an experimental version and can be changed at any time
    def _version3_experimental_fmt(build: Build) -> str:  # noqa: F821
        # Caches the hash value for faster lookup later
        if build.hash is not None:
            return build.hash

        # Adds namespace here to separate builds performed by different users
        # since all builds are stored in the same directory in v3, see
        # Build.build_path in orm.py. Additionally, this also hashes the
        # timestamp and build id just to make collisions very unlikely
        namespace_name = build.environment.namespace.name
        specification_hash = build.specification.sha256
        tzinfo = datetime.timezone.utc
        timestamp = int(build.scheduled_on.replace(tzinfo=tzinfo).timestamp())
        build_id = build.id
        hash_input = (
            namespace_name + specification_hash + str(timestamp) + str(build_id)
        )
        hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        hash = hash[: BuildKey._version3_experimental_hash_size]
        build.hash = hash
        return hash

    # version -> fmt function
    _fmt = {
        1: _version1_fmt,
        2: _version2_fmt,
        3: _version3_experimental_fmt,
    }

    @classmethod
    def _check_version(cls, build_key_version: int):
        if build_key_version not in cls.versions():
            raise ValueError(
                f"invalid build key version: {build_key_version}, "
                f"expected: {cls.versions()}"
            )

    @classmethod
    def set_current_version(cls, build_key_version: int) -> int:
        """Sets provided build key version as current and returns it"""
        cls._check_version(build_key_version)
        cls._current_version = build_key_version
        return build_key_version

    @classmethod
    def current_version(cls) -> int:
        """Returns currently selected build key version"""
        # None means the value is not set, likely due to an import error
        assert cls._current_version is not None
        return cls._current_version

    @classmethod
    def versions(cls) -> typing.Tuple[int]:
        """Returns available build key versions"""
        return tuple(cls._fmt.keys())

    @classmethod
    def get_build_key(cls, build: Build) -> str:  # noqa: F821
        """Returns build key for this build"""
        cls._check_version(build.build_key_version)
        return cls._fmt.get(build.build_key_version)(build)

    @classmethod
    def parse_build_key(
        cls,
        conda_store: CondaStore,
        build_key: str,  # noqa: F821
    ) -> int:
        """Returns build id from build key"""
        # This import is here to avoid cyclic imports
        from conda_store_server._internal import orm

        parts = build_key.split("-")
        # Note: cannot rely on the number of dashes to differentiate between
        # versions because name can contain dashes. Instead, this relies on the
        # hash size to infer the format. The name is the last field, so indexing
        # to find the id is okay.
        if build_key[cls._version2_hash_size] == "-":  # v2
            return int(parts[2])  # build_id
        elif "-" not in build_key:  # v3
            with conda_store.get_db() as db:
                build = db.query(orm.Build).filter(orm.Build.hash == build_key).first()
                if build is not None:
                    return build.id
                return None
        else:  # v1
            return int(parts[4])  # build_id
