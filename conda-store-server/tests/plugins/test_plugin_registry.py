# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest

from conda_store_server.plugins import BUILTIN_PLUGINS
from conda_store_server.plugins.plugin_registry import PluginRegistry
from conda_store_server import exception


class TestPlugin:
    @classmethod
    def name(cls):
        return "test-plugin"


def test_register_get_plugin():
    registry = PluginRegistry()
    test_plugin = TestPlugin()
    registry.register_plugin(test_plugin)

    assert registry.get_plugin("test-plugin") == test_plugin


def test_register_list_plugin():
    registry = PluginRegistry()
    test_plugin = TestPlugin()
    registry.register_plugin(test_plugin)

    assert len(registry.list_plugin_names()) == 1
    assert "test-plugin" in registry.list_plugin_names()


def test_collect_plugins():
    registry = PluginRegistry()
    registry.collect_plugins()
    registered = registry.registered.values()

    for plugin in BUILTIN_PLUGINS:
        assert plugin in registered


def test_register_same_plugin_multiple_times():
    registry = PluginRegistry()
    test_plugin = TestPlugin()
    
    registry.register_plugin(test_plugin)
    assert len(registry.list_plugin_names()) == 1
    assert "test-plugin" in registry.list_plugin_names()

    registry.register_plugin(test_plugin)
    assert len(registry.list_plugin_names()) == 1
    assert "test-plugin" in registry.list_plugin_names()


def test_register_plugin_duplicate_name():
    registry = PluginRegistry()
    
    test_plugin = TestPlugin()
    registry.register_plugin(test_plugin)
    assert len(registry.list_plugin_names()) == 1
    assert "test-plugin" in registry.list_plugin_names()

    class DuplicateNamePlugin:
        @classmethod
        def name(cls):
            return "test-plugin"
    
    duplicate = DuplicateNamePlugin()
    with pytest.raises(exception.CondaStorePluginAlreadyExistsError):
        registry.register_plugin(duplicate)
