# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pluggy

from conda_store_server.exception import CondaStorePluginNotFoundError
from conda_store_server.plugins import BUILTIN_PLUGINS
from conda_store_server.plugins.types import types


class PluginManager(pluggy.PluginManager):
    """
    PluginManager extends pluggy's plugin manager in order to extend
    functionality for
      * retrieving CondaStore type plugins (eg. TypeLockPlugin),
      * discovering and registering CondaStore plugins
    """

    def get_lock_plugins(self) -> dict[str, types.TypeLockPlugin]:
        """Returns a dict of lock plugin name to class"""
        plugins = [item for items in self.hook.lock_plugins() for item in items]
        return {p.name.lower(): p for p in plugins}

    def get_lock_plugin(self, name: str) -> types.TypeLockPlugin:
        """Returns a lock plugin by name"""
        lockers = self.get_lock_plugins()

        if name not in lockers:
            raise CondaStorePluginNotFoundError(
                plugin=name, available_plugins=lockers.keys()
            )

        return lockers[name]

    def collect_plugins(self) -> None:
        """Registers all availble plugins"""
        # TODO: support loading user defined plugins (eg. https://github.com/conda/conda/blob/cf3a0fa9ce01ada7a4a0c934e17be44b94d4eb91/conda/plugins/manager.py#L131)
        for plugin in BUILTIN_PLUGINS:
            self.register(plugin)
