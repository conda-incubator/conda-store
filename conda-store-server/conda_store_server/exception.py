# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import typing


class CondaStoreError(Exception):
    """Exception raised by conda store

    Attributes
    ----------
    message : str
        message to output to users
    """

    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class BuildPathError(CondaStoreError):
    """Exception raised by conda store when there is an issue with the requested build path

    Attributes
    ----------
    message : str
        message to output to users
    """


class CondaStorePluginNotFoundError(CondaStoreError):
    """Exception raised by conda store when a specified plugin is not found

    Attributes
    ----------
    plugin : str
        name of the plugin that was not found
    available_plugins : List[str]
        list of registered plugins
    """

    def __init__(self, plugin: str, available_plugins: typing.List[str]):
        self.message = f"Plugin {plugin} was requested but not found! The following plugins are available: {', '.join(available_plugins)}"
        super().__init__(self.message)
