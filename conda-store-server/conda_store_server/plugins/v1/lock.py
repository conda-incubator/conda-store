# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import typing

from conda_store_server._internal import conda_utils, schema
from conda_store_server.plugins.plugin_context import PluginContext


class LockPlugin:
    """
    Interface for the lock plugin. This plugin is responsible for solving the
    environment given some set of packages.

      * :meth: `lock_environment`
    """

    def lock_environment(
        self,
        context: PluginContext,
        spec: schema.CondaSpecification,
        platforms: typing.List[str] = [conda_utils.conda_platform()],
    ) -> str:
        """
        Solve the environment and generate a lockfile for a given spec on given platforms

        :param context: plugin context for execution
        :param spec: the conda specification to solve
        :param platforms: list of platforms (or subdirs) to solve for
        :return: string contents of the lockfile
        """
        raise NotImplementedError
