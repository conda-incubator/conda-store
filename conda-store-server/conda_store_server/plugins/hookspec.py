# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import typing

import pluggy

from conda_store_server._internal import conda_utils, schema
from conda_store_server.plugins import plugin_context

spec_name = "conda-store-server"

hookspec = pluggy.HookspecMarker(spec_name)

hookimpl = pluggy.HookimplMarker(spec_name)


class CondaStoreSpecs:
    """Conda Store hookspecs"""

    @hookspec(firstresult=True)
    def lock_environment(
        self,
        context: plugin_context.PluginContext,
        spec: schema.CondaSpecification,
        platforms: typing.List[str] = [conda_utils.conda_platform()],
    ) -> str:
        """Lock spec"""
