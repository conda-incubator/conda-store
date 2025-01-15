# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import datetime
import enum
import functools
import re
from typing import Annotated, Dict, List, TypeAlias

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
)

from conda_store_server._internal.schema import ALLOWED_CHARACTERS

# An ARN is a string which matches namespaces and environments. For example:
#     */*          matches all environments
#     */team       matches all environments named 'team' in any namespace
#
# Namespaces and environment names cannot contain "*" ":" "#" " " "/"
ARN_ALLOWED = f"^([{ALLOWED_CHARACTERS}*]+)/([{ALLOWED_CHARACTERS}*]+)$"
ARN_ALLOWED_REGEX = re.compile(ARN_ALLOWED)


def _datetime_factory(offset: datetime.timedelta):
    """Utcnow datetime + timezone as string"""
    return datetime.datetime.utcnow() + offset


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
