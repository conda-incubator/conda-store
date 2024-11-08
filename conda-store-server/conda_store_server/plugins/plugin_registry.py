# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from conda_store_server.plugins import BUILTIN_PLUGINS


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
        if plugin_name not in self.registered:
            self.registered[plugin_name] = p

    def collect_plugins(self):
        """Registers all availble plugins with the plugin registry"""
        for plugin in BUILTIN_PLUGINS:
            self.register_plugin(plugin)
