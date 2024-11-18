# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


class CondaStoreError(Exception):
    pass


class CondaStorePluginNotFoundError(CondaStoreError):
    """Exception raised by conda store when a specified plugin is not found
    Attributes:
        plugin -- plugin that was not found
        available_plugins -- list of registered plugins
    """

    def __init__(self, plugin, available_plugins):
        self.message = f"Plugin {plugin} was requested but not found! The following plugins are available {','.join(available_plugins)}"
        super().__init__(self.message)


class CondaStorePluginAlreadyExistsError(CondaStoreError):
    """Exception raised by conda store when a plugin with a duplicate name is registered
    Attributes:
        plugin_name -- name of the plugin attempted to be registered
    """

    def __init__(self, plugin_name):
        self.message = f"Plugin {plugin_name} was requested to be registered. However, a different plugin with that name already exists!"
        super().__init__(self.message)
