# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import sys

from sqlalchemy.orm import Session
from traitlets import (
    Bool,
    Callable,
    Integer,
    List,
    TraitError,
    Type,
    Unicode,
    default,
    validate,
)
from traitlets.config import LoggingConfigurable

from conda_store_server import CONDA_STORE_DIR, BuildKey, api, registry, storage
from conda_store_server._internal import conda_utils, environment, schema, utils


class CondaStore(LoggingConfigurable):
    storage_class = Type(
        default_value=storage.LocalStorage,
        klass=storage.Storage,
        allow_none=False,
        config=True,
    )

    container_registry_class = Type(allow_none=True, help="(deprecated)")

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
        help="Build key version to use: 1 (long, legacy), 2 (shorter hash, default), 3 (hash-only, experimental)",
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
        help="Conda platforms to solve environments for via conda-lock. Must include current platform.",
        config=True,
    )

    conda_channel_alias = Unicode(
        "https://conda.anaconda.org",
        help="The prepended url location to associate with channel names",
        config=True,
    )

    conda_flags = Unicode(
        "--strict-channel-priority",
        help="The flags to be passed through the CONDA_FLAGS environment variable during the environment build",
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

    lock_backend = Unicode(
        default_value="conda-lock",
        allow_none=False,
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
                import redis
                r = redis.Redis.from_url(self.redis_url)
                r.ping()
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

    post_update_environment_build_hook = Callable(
        default_value=None,
        help="callable function taking conda_store and `orm.Environment` object as input arguments. This function can be used to add custom behavior that will run after an environment's current build changes.",
        config=True,
        allow_none=True,
    )
