# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest

from conda_store_server.plugins import BUILTIN_PLUGINS, types
from conda_store_server._internal.plugins.lock.conda_lock import conda_lock
from conda_store_server.exception import CondaStorePluginNotFoundError

    
def test_collect_plugins(plugin_manager):
    plugin_manager.collect_plugins()
    for plugin in BUILTIN_PLUGINS:
        assert plugin_manager.is_registered(plugin)


def test_get_lock_plugins(plugin_manager):
    plugin_manager.collect_plugins()
    lp = plugin_manager.get_lock_plugins()
    
    # Ensure built in lock plugins are accounted for
    assert "conda-lock" in lp

    # Ensure all plugins are lock plugins
    for plugin in lp.values():
        assert isinstance(plugin, types.TypeLockPlugin) 


def get_lock_plugin(plugin_manager):
    plugin_manager.collect_plugins()
    lp = plugin_manager.lock_plugin("conda-lock")
    assert lp.name == "conda-lock"
    assert lp.backend == conda_lock.CondaLock


def get_lock_plugin_does_not_exist(plugin_manager):
    plugin_manager.collect_plugins()
    with pytest.raises(CondaStorePluginNotFoundError):
        plugin_manager.lock_plugin("i really don't exist")
