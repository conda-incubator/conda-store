import datetime
import enum
from typing import List, Optional, Union

from pydantic import BaseModel


class CondaPackage(BaseModel):
    id: int
    channel: str
    license: str
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

    class Config:
        orm_mode = True


class CondaSpecificationPip(BaseModel):
    pip: List[str]


class CondaSpecification(BaseModel):
    name: str
    channels: Optional[List[str]]
    dependencies: List[Union[str, CondaSpecificationPip]]
    prefix: Optional[str]
