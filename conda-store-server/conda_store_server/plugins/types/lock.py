# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import typing

from conda_store_server._internal import schema, conda_utils
from conda_store_server.plugin import action_context


class LockPlugin():
    @classmethod
    def name(cls) -> str:
        """Name of the plugin"""
        raise NotImplementedError
    
    def synopsis(self) -> str:
        """Short synopsis of what the plugin does"""
        raise NotImplementedError
    
    def lock_environment(
        self,
        context,
        spec: schema.CondaSpecification,
        platforms: typing.List[str] = [conda_utils.conda_platform()]
    ) -> action_context.ActionContext:
        """Solve the environment and generate a lockfile for a given spec on given platforms"""
        raise NotImplementedError

    def to_environment_spec(self, env_spec):
        # TODO: this should return a conda-store environment spec (this still needs to be defined still)
        """Converts the plugin's notion of an environment spec to a conda-store lock spec"""
        raise NotImplementedError

    def from_environment_spec(self, env_spec):
        # TODO: this should take a conda-store environment spec as a parameter
        """Converts a conda-store lock speck to the plugin's notion of a lock spec"""
        raise NotImplementedError