# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from conda_store_server.plugins import BUILTIN_PLUGINS
from conda_store_server import exception


class PluginRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # plugins are registered in the map of the form:
        # {plugin_name: plugin_class}
        self.registered = {}

    def list_plugin_names(self):
        return self.registered.keys()

    def get_plugin(self, name):
        return self.registered.get(name)

    def register_plugin(self, p):
        """Adds plugin to the list of registered plugins"""
        plugin_name = p.name()
        if plugin_name in self.registered:
            # check that no different plugin with the same name is already registered
            if p is not self.registered[plugin_name]:
                raise exception.CondaStorePluginAlreadyExistsError(plugin_name)
        else:
            self.registered[plugin_name] = p

    def collect_plugins(self):
        """Registers all availble plugins with the plugin registry"""
        # TODO: support loading user defined plugins (eg. https://github.com/conda/conda/blob/cf3a0fa9ce01ada7a4a0c934e17be44b94d4eb91/conda/plugins/manager.py#L131)
        for plugin in BUILTIN_PLUGINS:
            self.register_plugin(plugin)
