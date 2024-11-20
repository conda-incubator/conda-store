# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from conda_store_server.plugins import BUILTIN_PLUGINS

    
def test_collect_plugins(plugin_manager):
    plugin_manager.collect_plugins()
    for plugin in BUILTIN_PLUGINS:
        assert plugin_manager.is_registered(plugin)
