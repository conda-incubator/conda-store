import datetime
import enum
from typing import List, Optional, Union, Dict

from pydantic import BaseModel, Field


def docker_datetime_factory():
    """utcnow datetime + timezone as string"""
    return datetime.datetime.utcnow().astimezone().isoformat()


class CondaPackage(BaseModel):
    id: int
    channel: str
    license: Optional[str]
    sha256: str
    name: str
    version: str

    class Config:
        orm_mode = True


class Build(BaseModel):
    id: int
    specification_id: int
    packages: List[CondaPackage]
    status: enum.Enum
    size: int
    scheduled_on: datetime.datetime
    started_on: Optional[datetime.datetime]
    ended_on: Optional[datetime.datetime]

    class Config:
        orm_mode = True
        use_enum_values = True


class Specification(BaseModel):
    id: int
    name: str
    spec: dict
    sha256: str
    created_on: datetime.datetime
    builds: List[Build]

    class Config:
        orm_mode = True


class Environment(BaseModel):
    id: int
    namespace: str
    name: str
    build_id: Optional[int]
    specification_id: Optional[int]
    specification: Optional[Specification]

    class Config:
        orm_mode = True

# Conda Environment
class CondaSpecificationPip(BaseModel):
    pip: List[str]


class CondaSpecification(BaseModel):
    name: str
    channels: Optional[List[str]]
    dependencies: List[Union[str, CondaSpecificationPip]]
    prefix: Optional[str]


# Docker Registry
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
    Env: List[str] = ["PATH=/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
    Cmd: List[str] = ["/bin/sh"]
    ArgsEscaped: bool = True
    Image: Optional[str] = None
    Volumes: Optional[List[str]]
    WorkingDir: str = ""
    Entrypoint: Optional[str] = None
    OnBuild: Optional[str] = None
    Labels: Optional[Dict[str, str]] = {
        'conda_store': '0.0.1'
    }


class DockerConfigRootFS(BaseModel):
    type: str = "layers"
    diff_ids: List[str] = []


class DockerConfigHistory(BaseModel):
    created: str = Field(default_factory=docker_datetime_factory)
    created_by: str = ""


class DockerConfig(BaseModel):
    architecture: str = "amd64"
    os: str = "linux"
    config: DockerConfigConfig
    container: str
    container_config: DockerConfigConfig
    created: str = Field(default_factory=docker_datetime_factory)
    docker_version: str = "18.09.7"
    history: List[DockerConfigHistory] = []
    rootfs: DockerConfigRootFS
