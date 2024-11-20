# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pluggy

from conda_store_server.exception import CondaStorePluginNotFoundError
from conda_store_server.plugins import BUILTIN_PLUGINS
from conda_store_server.plugins import types


class PluginManager(pluggy.PluginManager):
    def get_lock_plugins(self):
        """Returns a dict of lock plugin name to class"""
        plugins = [item for items in self.hook.lock_plugins() for item in items]
        return {
            p.name.lower(): p
            for p in plugins
        }
    
    def lock_plugin(self, name=None):
        """Returns a lock plugin by name. If none is given, the default plugin is used"""
        lockers = self.get_lock_plugins()

        if name is None:
            name = "lock-conda_lock"
        
        if name not in lockers.keys():
            raise CondaStorePluginNotFoundError(
                plugin=name,
                available_plugins=lockers.keys()
            )
        target = lockers.get(name)
        
        return target.backend()
    
    def collect_plugins(self):
        """Registers all availble plugins"""
        # TODO: support loading user defined plugins (eg. https://github.com/conda/conda/blob/cf3a0fa9ce01ada7a4a0c934e17be44b94d4eb91/conda/plugins/manager.py#L131)
        for plugin in BUILTIN_PLUGINS:
            self.register(plugin)
