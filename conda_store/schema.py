import datetime
from typing import List, Optional

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
    status: str
    size: int
    scheduled_on: datetime.datetime
    started_on: datetime.datetime
    ended_on: datetime.datetime

    class Config:
        orm_mode = True


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
