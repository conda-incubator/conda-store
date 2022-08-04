import re
import datetime
import enum
from typing import List, Optional, Union, Dict, Any
import functools

from pydantic import BaseModel, Field, constr, validator


def _datetime_factory(offset: datetime.timedelta):
    """utcnow datetime + timezone as string"""
    return datetime.datetime.utcnow() + offset


# namespace and name cannot contain "*" ":" "#" " " "/"
# this is a more restrictive list
ALLOWED_CHARACTERS = "A-Za-z0-9-+_@$&?^~.="
ARN_ALLOWED = f"^([{ALLOWED_CHARACTERS}*]+)/([{ALLOWED_CHARACTERS}*]+)$"


#########################
# Authentication Schema
#########################


class Permissions(enum.Enum):
    ENVIRONMENT_CREATE = "environment:create"
    ENVIRONMENT_READ = "environment::read"
    ENVIRONMENT_UPDATE = "environment::update"
    ENVIRONMENT_DELETE = "environment::delete"
    BUILD_DELETE = "build::delete"
    NAMESPACE_CREATE = "namespace::create"
    NAMESPACE_READ = "namespace::read"
    NAMESPACE_DELETE = "namespace::delete"


class AuthenticationToken(BaseModel):
    exp: datetime.datetime = Field(
        default_factory=functools.partial(_datetime_factory, datetime.timedelta(days=1))
    )
    primary_namespace: str = "default"
    role_bindings: Dict[constr(regex=ARN_ALLOWED), List[str]] = {}


##########################
# Database Schema
##########################


class StorageBackend(enum.Enum):
    FILESYSTEM = "filesystem"
    S3 = "s3"


class CondaChannel(BaseModel):
    id: int
    name: str
    last_update: Optional[datetime.datetime]

    class Config:
        orm_mode = True


class CondaPackage(BaseModel):
    id: int
    channel: CondaChannel
    build: str
    license: Optional[str]
    sha256: str
    name: str
    version: str
    summary: Optional[str]

    class Config:
        orm_mode = True


class Namespace(BaseModel):
    id: int
    name: constr(regex=f"^[{ALLOWED_CHARACTERS}]+$")  # noqa: F722

    class Config:
        orm_mode = True


class Specification(BaseModel):
    id: int
    name: str
    spec: dict
    sha256: str
    created_on: datetime.datetime

    class Config:
        orm_mode = True


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


class BuildArtifact(BaseModel):
    id: int
    artifact_type: BuildArtifactType
    key: str

    class Config:
        orm_mode = True
        use_enum_values = True


class Build(BaseModel):
    id: int
    environment_id: int
    specification: Optional[Specification]
    packages: Optional[List[CondaPackage]]
    status: BuildStatus
    size: int
    scheduled_on: datetime.datetime
    started_on: Optional[datetime.datetime]
    ended_on: Optional[datetime.datetime]
    build_artifacts: Optional[List[BuildArtifact]]

    class Config:
        orm_mode = True
        use_enum_values = True


class Environment(BaseModel):
    id: int
    namespace: Namespace
    name: str
    current_build_id: int
    current_build: Optional[Build]

    class Config:
        orm_mode = True


# Conda Environment
class CondaSpecificationPip(BaseModel):
    pip: List[str] = []

    @validator("pip", each_item=True)
    def check_pip(cls, v):
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
                raise ValueError(f"Invalid pypi package dependency {v}")

        return v


class CondaSpecification(BaseModel):
    name: constr(regex=f"^[{ALLOWED_CHARACTERS}]+$")  # noqa: F722
    channels: List[str] = []
    dependencies: List[Union[str, CondaSpecificationPip]] = []
    prefix: Optional[str]

    @validator("dependencies", each_item=True)
    def check_dependencies(cls, v):
        from conda.models.match_spec import MatchSpec

        if not isinstance(v, str):
            return v  # ignore pip field

        try:
            MatchSpec(v)
        except Exception as e:
            print(e)
            raise ValueError(f"Invalid conda package dependency specification {v}")

        return v


###############################
#  Docker Registry Schema
###############################


def _docker_datetime_factory():
    """utcnow datetime + timezone as string"""
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
    Volumes: Optional[List[str]]
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
    data: Optional[Any]
    message: Optional[str]


class APIPaginatedResponse(APIResponse):
    page: int
    size: int
    count: int


class APIAckResponse(BaseModel):
    status: APIStatus
    message: Optional[str]


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
    expiration: Optional[datetime.datetime]


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
