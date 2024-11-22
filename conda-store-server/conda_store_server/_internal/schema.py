# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import datetime
import enum
import functools
import os
import re
import sys
from typing import Annotated, Any, Callable, Dict, List, Optional, TypeAlias, Union

from conda_lock.lockfile.v1.models import Lockfile
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
)

from conda_store_server._internal import conda_utils, utils


def _datetime_factory(offset: datetime.timedelta):
    """Utcnow datetime + timezone as string"""
    return datetime.datetime.utcnow() + offset


# An ARN is a string which matches namespaces and environments. For example:
#     */*          matches all environments
#     */team       matches all environments named 'team' in any namespace
#
# Namespaces and environment names cannot contain "*" ":" "#" " " "/"
ALLOWED_CHARACTERS = "A-Za-z0-9-+_@$&?^~.="
ARN_ALLOWED = f"^([{ALLOWED_CHARACTERS}*]+)/([{ALLOWED_CHARACTERS}*]+)$"
ARN_ALLOWED_REGEX = re.compile(ARN_ALLOWED)


#########################
# Authentication Schema
#########################

RoleBindings: TypeAlias = Dict[
    Annotated[str, StringConstraints(pattern=ARN_ALLOWED)], List[str]
]


class Permissions(enum.Enum):
    """Permissions map to conda-store actions"""

    ENVIRONMENT_CREATE = "environment:create"
    ENVIRONMENT_READ = "environment::read"
    ENVIRONMENT_UPDATE = "environment::update"
    ENVIRONMENT_DELETE = "environment::delete"
    ENVIRONMENT_SOLVE = "environment::solve"
    BUILD_CANCEL = "build::cancel"
    BUILD_DELETE = "build::delete"
    NAMESPACE_CREATE = "namespace::create"
    NAMESPACE_READ = "namespace::read"
    NAMESPACE_UPDATE = "namespace::update"
    NAMESPACE_DELETE = "namespace::delete"
    NAMESPACE_ROLE_MAPPING_CREATE = "namespace-role-mapping::create"
    NAMESPACE_ROLE_MAPPING_READ = "namespace-role-mapping::read"
    NAMESPACE_ROLE_MAPPING_UPDATE = "namespace-role-mapping::update"
    NAMESPACE_ROLE_MAPPING_DELETE = "namespace-role-mapping::delete"
    SETTING_READ = "setting::read"
    SETTING_UPDATE = "setting::update"


class AuthenticationToken(BaseModel):
    exp: datetime.datetime = Field(
        default_factory=functools.partial(_datetime_factory, datetime.timedelta(days=1))
    )
    primary_namespace: str = "default"
    role_bindings: RoleBindings = {}


##########################
# Database Schema
##########################


class StorageBackend(enum.Enum):
    FILESYSTEM = "filesystem"
    S3 = "s3"


class CondaChannel(BaseModel):
    id: int
    name: str
    last_update: Optional[datetime.datetime] = None
    model_config = ConfigDict(from_attributes=True)


class CondaPackageBuild(BaseModel):
    id: int
    build: str
    sha256: str
    model_config = ConfigDict(from_attributes=True)


class CondaPackage(BaseModel):
    id: int
    channel: CondaChannel
    license: Optional[str] = None
    name: str
    version: str
    summary: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class NamespaceRoleMapping(BaseModel):
    id: int
    entity: str
    role: str
    model_config = ConfigDict(from_attributes=True)


class NamespaceRoleMappingV2(BaseModel):
    id: int
    namespace: str
    other_namespace: str
    role: str
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_list(cls, lst):
        return cls(**{k: v for k, v in zip(cls.model_fields.keys(), lst, strict=False)})


class Namespace(BaseModel):
    id: int
    name: Annotated[str, StringConstraints(pattern=f"^[{ALLOWED_CHARACTERS}]+$")]  # noqa: F722
    metadata_: Dict[str, Any] = None
    role_mappings: List[NamespaceRoleMapping] = []
    model_config = ConfigDict(from_attributes=True)


class Specification(BaseModel):
    id: int
    name: str
    spec: dict
    sha256: str
    created_on: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


# Use str mixin to allow pydantic to serialize Settings models
class BuildArtifactType(str, enum.Enum):
    DIRECTORY = "DIRECTORY"
    LOCKFILE = "LOCKFILE"
    LOGS = "LOGS"
    YAML = "YAML"
    CONDA_PACK = "CONDA_PACK"
    DOCKER_BLOB = "DOCKER_BLOB"
    DOCKER_MANIFEST = "DOCKER_MANIFEST"
    CONTAINER_REGISTRY = "CONTAINER_REGISTRY"
    CONSTRUCTOR_INSTALLER = "CONSTRUCTOR_INSTALLER"


class BuildStatus(enum.Enum):
    QUEUED = "QUEUED"
    BUILDING = "BUILDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class BuildArtifact(BaseModel):
    id: int
    artifact_type: BuildArtifactType
    key: str
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class Build(BaseModel):
    id: int
    environment_id: int
    specification: Optional[Specification] = None
    packages: Optional[List[CondaPackage]] = None
    status: BuildStatus
    status_info: Optional[str] = None
    size: int
    scheduled_on: datetime.datetime
    started_on: Optional[datetime.datetime] = None
    ended_on: Optional[datetime.datetime] = None
    build_artifacts: Optional[List[BuildArtifact]] = None
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class Environment(BaseModel):
    id: int
    namespace: Namespace
    name: str
    current_build_id: int
    current_build: Optional[Build] = None

    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class Settings(BaseModel):
    default_namespace: str = Field(
        "default",
        description="default namespace for conda-store",
        metadata={"global": True},
    )

    filesystem_namespace: str = Field(
        "filesystem",
        description="namespace to use for environments picked up via `CondaStoreWorker.watch_paths` on the filesystem",
        metadata={"global": True},
    )

    default_uid: Optional[int] = Field(
        None if sys.platform == "win32" else os.getuid(),
        description="default uid to assign to built environments",
        metadata={"global": True},
    )

    default_gid: Optional[int] = Field(
        None if sys.platform == "win32" else os.getgid(),
        description="default gid to assign to built environments",
        metadata={"global": True},
    )

    default_permissions: Optional[str] = Field(
        None if sys.platform == "win32" else "775",
        description="default file permissions to assign to built environments",
        metadata={"global": True},
    )

    storage_threshold: int = Field(
        5 * 1024**3,
        description="Storage threshold in bytes of minimum available storage required in order to perform builds",
        metadata={"global": True},
    )

    conda_command: str = Field(
        "mamba",
        description="conda executable to use for solves",
        metadata={"global": True},
    )

    conda_platforms: List[str] = Field(
        ["noarch", conda_utils.conda_platform()],
        description="Conda platforms to download package repodata.json from. By default includes current architecture and noarch",
        metadata={"global": True},
    )

    conda_max_solve_time: int = Field(
        5 * 60,  # 5 minute
        description="Maximum time in seconds to allow for solving a given conda environment",
        metadata={"global": True},
    )

    conda_indexed_channels: List[str] = Field(
        ["main", "conda-forge", "https://repo.anaconda.com/pkgs/main"],
        description="Conda channels to be indexed by conda-store at start.  Defaults to main and conda-forge.",
        metadata={"global": True},
    )

    build_artifacts_kept_on_deletion: List[BuildArtifactType] = Field(
        [
            BuildArtifactType.LOGS,
            BuildArtifactType.LOCKFILE,
            BuildArtifactType.YAML,
            # no possible way to delete these artifacts
            # in most container registries via api
            BuildArtifactType.CONTAINER_REGISTRY,
        ],
        description="artifacts to keep on build deletion",
        metadata={"global": True},
    )

    conda_solve_platforms: List[str] = Field(
        [conda_utils.conda_platform()],
        description="Conda platforms to solve environments for via conda-lock. Must include current platform.",
        metadata={"global": False},
    )

    conda_channel_alias: str = Field(
        "https://conda.anaconda.org",
        description="prepended url to associate with channel names",
        metadata={"global": False},
    )

    conda_default_channels: List[str] = Field(
        ["conda-forge"],
        description="channels that by default are included if channels are empty",
        metadata={"global": False},
    )

    conda_allowed_channels: List[str] = Field(
        [],
        description=(
            "Allowed conda channels to be used in conda environments. "
            "If set to empty list all channels are accepted (default). "
            "Example: "
            '["main", "conda-forge", "https://repo.anaconda.com/pkgs/main"]'
        ),
        metadata={"global": False},
    )

    conda_default_packages: List[str] = Field(
        [],
        description="Conda packages that included by default if none are included",
        metadata={"global": False},
    )

    conda_required_packages: List[str] = Field(
        [],
        description="Conda packages that are required to be within environment specification. Will raise a validation error is package not in specification",
        metadata={"global": False},
    )

    conda_included_packages: List[str] = Field(
        [],
        description="Conda packages that auto included within environment specification. Will not raise a validation error if package not in specification and will be auto added",
        metadata={"global": False},
    )

    pypi_default_packages: List[str] = Field(
        [],
        description="PyPi packages that included by default if none are included",
        metadata={"global": False},
    )

    pypi_required_packages: List[str] = Field(
        [],
        description="PyPi packages that are required to be within environment specification. Will raise a validation error is package not in specification",
        metadata={"global": False},
    )

    pypi_included_packages: List[str] = Field(
        [],
        description="PyPi packages that auto included within environment specification. Will not raise a validation error if package not in specification and will be auto added",
        metadata={"global": False},
    )

    build_artifacts: List[BuildArtifactType] = Field(
        [
            BuildArtifactType.LOCKFILE,
            BuildArtifactType.YAML,
            BuildArtifactType.CONDA_PACK,
            BuildArtifactType.CONSTRUCTOR_INSTALLER,
            *(
                [
                    BuildArtifactType.DOCKER_MANIFEST,
                    BuildArtifactType.CONTAINER_REGISTRY,
                ]
                if sys.platform == "linux"
                else []
            ),
        ],
        description="artifacts to build in conda-store. By default all of the artifacts",
        metadata={"global": False},
    )

    default_docker_base_image: Union[str, Callable] = Field(
        "registry-1.docker.io/library/debian:sid-slim",
        description="default base image used for the Dockerized environments. Make sure to have a proper glibc within image (highly discourage alpine/musl based images). Can also be callable function which takes the `orm.Build` object as input which has access to all attributes about the build such as install packages, requested packages, name, namespace, etc",
        metadata={"global": False},
    )


PipArg = Annotated[str, AfterValidator(lambda v: check_pip(v))]


# Conda Environment
class CondaSpecificationPip(BaseModel):
    pip: List[PipArg] = []


CondaDep = Annotated[str, AfterValidator(lambda v: check_dependencies(v))]


class CondaSpecification(BaseModel):
    channels: List[str] = []
    dependencies: List[CondaDep | CondaSpecificationPip] = []
    description: Optional[str] = ""
    name: Annotated[str, StringConstraints(pattern=f"^[{ALLOWED_CHARACTERS}]+$")]
    prefix: Optional[str] = None
    variables: Optional[Dict[str, Union[str, int]]] = None

    @classmethod
    def parse_obj(cls, specification):
        try:
            return super().parse_obj(specification)
        except ValidationError as e:
            # there can be multiple errors. Let's build a comprehensive summary
            # to return to the end user.

            # hr stands for "human readable"
            all_errors_hr = []

            for err in e.errors():
                error_type = err["type"]
                error_loc = err["loc"]

                # fallback case : if we can't figure out the error, let's build a default
                # one based on the data returned by Pydantic.
                human_readable_error = (
                    f"{err['msg']} (type={error_type}, loc={error_loc})"
                )

                if error_type == "type_error.none.not_allowed":
                    if error_loc[0] == "name":
                        human_readable_error = (
                            "The name of the environment cannot be empty."
                        )
                    else:
                        if len(error_loc) == 1:
                            human_readable_error = f"Invalid YAML : A forbidden `None` value has been encountered in section {error_loc[0]}"
                        elif len(error_loc) == 2:
                            human_readable_error = f"Invalid YAML : A forbidden `None` value has been encountered in section `{error_loc[0]}`, line {error_loc[1]}"

                all_errors_hr.append(human_readable_error)

            raise utils.CondaStoreError(all_errors_hr)


class LockfileSpecification(BaseModel):
    name: Annotated[str, StringConstraints(pattern=f"^[{ALLOWED_CHARACTERS}]+$")]  # noqa: F722
    description: Optional[str] = ""
    lockfile: Lockfile

    @classmethod
    def parse_obj(cls, specification):
        # To show a human-readable error if no data is provided
        specification = {} if specification is None else specification
        # This uses pop because the version field must not be part of Lockfile
        # input. Otherwise, the input will be rejected. The version field is
        # hardcoded in the Lockfile schema and is only used when the output is
        # printed. So the code below validates that the version is 1 if present
        # and removes it to avoid the mentioned parsing error.
        lockfile = specification.get("lockfile")
        version = lockfile and lockfile.pop("version", None)
        if version not in (None, 1):
            raise ValidationError(
                "Expected lockfile to have no version field, or version=1",
            )

        return super().parse_obj(specification)

    def model_dump(self):
        res = super().model_dump()
        # The dict_for_output method includes the version field into the output
        # and excludes unset fields. Without the version field present,
        # conda-lock would reject a lockfile during parsing, so it wouldn't be
        # installable, that's why we need to include the version
        res["lockfile"] = self.lockfile.dict_for_output()
        return res

    def __str__(self):
        # This makes sure the format is suitable for output if this object is
        # converted to a string, which can also happen implicitly
        return str(self.dict())


###############################
#  Docker Registry Schema
###############################


def _docker_datetime_factory():
    """Utcnow datetime + timezone as string"""
    return datetime.datetime.utcnow().astimezone().isoformat()


class DockerManifestLayer(BaseModel):
    mediaType: str = "application/vnd.docker.image.rootfs.diff.tar.gzip"
    size: int
    digest: str


class DockerManifestConfig(BaseModel):
    mediaType: str = "application/vnd.docker.container.image.v1+json"
    size: int
    digest: str


class DockerManifest(BaseModel):
    schemaVersion: int = 2
    mediaType: str = "application/vnd.docker.distribution.manifest.v2+json"
    config: DockerManifestConfig
    layers: List[DockerManifestLayer] = []


class DockerConfigConfig(BaseModel):
    Hostname: str = ""
    Domainname: str = ""
    User: str = ""
    AttachStdin: bool = False
    AttachStdout: bool = False
    AttachStderr: bool = False
    Tty: bool = False
    OpenStdin: bool = False
    StdinOnce: bool = False
    Env: List[str] = [
        "PATH=/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    ]
    Cmd: List[str] = ["/bin/sh"]
    ArgsEscaped: bool = True
    Image: Optional[str] = None
    Volumes: Optional[List[str]] = None
    WorkingDir: str = ""
    Entrypoint: Optional[str] = None
    OnBuild: Optional[str] = None
    Labels: Optional[Dict[str, str]] = {"conda_store": "0.0.1"}


class DockerConfigRootFS(BaseModel):
    type: str = "layers"
    diff_ids: List[str] = []


class DockerConfigHistory(BaseModel):
    created: str = Field(default_factory=_docker_datetime_factory)
    created_by: str = ""


class DockerConfig(BaseModel):
    architecture: str = "amd64"
    os: str = "linux"
    config: DockerConfigConfig
    container: str
    container_config: DockerConfigConfig
    created: str = Field(default_factory=_docker_datetime_factory)
    docker_version: str = "18.09.7"
    history: List[DockerConfigHistory] = []
    rootfs: DockerConfigRootFS


# https://docs.docker.com/registry/spec/api/#errors-2
class DockerRegistryError(enum.Enum):
    NAME_UNKNOWN = {
        "message": "repository name not known to registry",
        "detail": "This is returned if the name used during an operation is unknown to the registry",
        "status": 404,
    }
    BLOB_UNKNOWN = {
        "message": "blob unknown to registry",
        "detail": "This error may be returned when a blob is unknown to the registry in a specified repository. This can be returned with a standard get or if a manifest references an unknown layer during upload",
        "status": 404,
    }
    MANIFEST_UNKNOWN = {
        "message": "manifest unknown",
        "detail": "This error is returned when the manifest, identified by name and tag is unknown to the repository",
        "status": 404,
    }
    UNAUTHORIZED = {
        "message": "authentication required",
        "detail": "The access controller was unable to authenticate the client. Often this will be accompanied by a Www-Authenticate HTTP response header indicating how to authenticate",
        "status": 401,
    }
    UNSUPPORTED = {
        "message": "The operation is unsupported",
        "detail": "The operation was unsupported due to a missing implementation or invalid set of parameters",
        "status": 405,
    }
    DENIED = {
        "message": "requested access to the resource is denied",
        "detail": "The access controller denied access for the operation on a resource",
        "status": 403,
    }


# API Response Objects
class APIStatus(enum.Enum):
    OK = "ok"
    ERROR = "error"


class APIResponse(BaseModel):
    status: APIStatus
    data: Optional[Any] = None
    message: Optional[str] = None


class APIPaginatedResponse(APIResponse):
    page: int
    size: int
    count: int


class APIAckResponse(BaseModel):
    status: APIStatus
    message: Optional[str] = None


# GET /api/v1
class APIGetStatusData(BaseModel):
    version: str


class APIGetStatus(APIResponse):
    data: APIGetStatusData


# GET /api/v1/permission
class APIGetPermissionData(BaseModel):
    authenticated: bool
    primary_namespace: str
    entity_permissions: Dict[str, List[str]]
    entity_roles: Dict[str, List[str]]
    expiration: Optional[datetime.datetime] = None


class APIGetPermission(APIResponse):
    data: APIGetPermissionData


# POST /api/v1/token
class APIPostTokenData(BaseModel):
    token: str


class APIPostToken(APIResponse):
    data: APIPostTokenData


# GET /api/v1/namespace
class APIListNamespace(APIPaginatedResponse):
    data: List[Namespace]


# GET /api/v1/namespace/{name}
class APIGetNamespace(APIResponse):
    data: Namespace


# POST /api/v1/namespace/{name}/role
class APIPostNamespaceRole(BaseModel):
    other_namespace: str
    role: str


# PUT /api/v1/namespace/{name}/role
class APIPutNamespaceRole(BaseModel):
    other_namespace: str
    role: str


# DELETE /api/v1/namespace/{name}/role
class APIDeleteNamespaceRole(BaseModel):
    other_namespace: str


# GET /api/v1/environment
class APIListEnvironment(APIPaginatedResponse):
    data: List[Environment]


# GET /api/v1/environment/{namespace}/{name}
class APIGetEnvironment(APIResponse):
    data: Environment


# GET /api/v1/specification
class APIGetSpecificationFormat(enum.Enum):
    YAML = "yaml"
    LOCKFILE = "lockfile"


# POST /api/v1/specification
class APIPostSpecificationData(BaseModel):
    build_id: int


class APIPostSpecification(APIResponse):
    data: APIPostSpecificationData


# GET /api/v1/build
class APIListBuild(APIPaginatedResponse):
    data: List[Build]


# GET /api/v1/build/1
class APIGetBuild(APIResponse):
    data: Build


# GET /api/v1/channel
class APIListCondaChannel(APIPaginatedResponse):
    data: List[CondaChannel]


# GET /api/v1/package
class APIListCondaPackage(APIPaginatedResponse):
    data: List[CondaPackage]


# GET /api/v1/setting/*/*
class APIGetSetting(APIResponse):
    data: Dict[str, Any]


# PUT /api/v1/setting/*/*
class APIPutSetting(APIResponse):
    pass


# GET /api/v1/usage/
class APIGetUsage(APIResponse):
    data: Dict[str, Dict[str, Any]]


def check_pip(v: str) -> str:
    """Check that pip options and dependencies are valid.

    Parameters
    ----------
    v : str
        Pip package name or CLI arg to validate

    Returns
    -------
    str
        Validated pip package name or CLI arg
    """
    from pkg_resources import Requirement

    allowed_pip_params = ["--index-url", "--extra-index-url", "--trusted-host"]

    if v.startswith("--"):
        match = re.fullmatch("(.+?)[ =](.*)", v)
        if match is None or match.group(1) not in allowed_pip_params:
            raise ValueError(
                f"Invalid pip option '{v}' supported options are {allowed_pip_params}"
            )
    else:
        try:
            Requirement.parse(v)
        except Exception:
            raise ValueError(
                f'Invalid pypi package dependency "{v}" ensure it follows peps https://peps.python.org/pep-0508/ and https://peps.python.org/pep-0440/'
            )

    return v


def check_dependencies(v: str | CondaSpecificationPip) -> str | CondaSpecificationPip:
    """Check that the dependency is either a list of pip args or a conda MatchSpec.

    Parameters
    ----------
    v : str | CondaSpecificationPip
        A list of pip args or a valid conda MatchSpec object

    Returns
    -------
    str | CondaSpecificationPip
        The validated dependency
    """
    from conda.models.match_spec import MatchSpec

    if not isinstance(v, str):
        return v  # ignore pip field

    try:
        MatchSpec(v)
    except Exception as e:
        print(e)
        raise ValueError(f"Invalid conda package dependency specification {v}")

    return v
