import datetime
import typing
from pathlib import Path

__version__ = "2024.3.1"


CONDA_STORE_DIR = Path.home() / ".conda-store"


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

    def _version1_fmt(build: "Build") -> str:  # noqa: F821
        datetime_format = "%Y%m%d-%H%M%S-%f"
        hash = build.specification.sha256
        timestamp = build.scheduled_on.strftime(datetime_format)
        id = build.id
        name = build.specification.name
        return f"{hash}-{timestamp}-{id}-{name}"

    def _version2_fmt(build: "Build") -> str:  # noqa: F821
        tzinfo = datetime.timezone.utc
        hash = build.specification.sha256[: BuildKey._version2_hash_size]
        timestamp = int(build.scheduled_on.replace(tzinfo=tzinfo).timestamp())
        id = build.id
        name = build.specification.name
        return f"{hash}-{timestamp}-{id}-{name}"

    # version -> fmt function
    _fmt = {
        1: _version1_fmt,
        2: _version2_fmt,
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
    def get_build_key(cls, build: "Build") -> str:  # noqa: F821
        """Returns build key for this build"""
        cls._check_version(build.build_key_version)
        return cls._fmt.get(build.build_key_version)(build)

    @classmethod
    def parse_build_key(cls, build_key: str) -> int:
        """Returns build id from build key"""
        parts = build_key.split("-")
        # Note: cannot rely on the number of dashes to differentiate between
        # versions because name can contain dashes. Instead, this relies on the
        # hash size to infer the format. The name is the last field, so indexing
        # to find the id is okay.
        if build_key[cls._version2_hash_size] == "-":  # v2
            return int(parts[2])  # build_id
        else:  # v1
            return int(parts[4])  # build_id
