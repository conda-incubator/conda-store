# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest

from conda_store_server import api
from conda_store_server._internal import schema
from conda_store_server._internal.settings import Settings


@pytest.fixture
def settings(db) -> Settings:
    default_settings = schema.Settings(
        default_uid = 999,
        default_gid = 999,
        conda_channel_alias = "defaultchannelalias"
    )

    # setup test global settings
    global_settings = {
        "default_uid": 888,
        "conda_channel_alias": "globalchannelalias",
        "conda_command": "myglobalcondacommand"
    }
    api.set_kvstore_key_values(db, "setting", global_settings)

    # setup test namespace settings
    namespace_settings =  {
        "conda_channel_alias": "namespacechannelalias",
        "conda_command": "mynamespacecondacommand",
        "conda_default_packages": ["ipykernel"]
    }
    api.set_kvstore_key_values(db, "setting/test_namespace", namespace_settings)

    # setup test namespace (two) settings
    namespace_two_settings =  {
        "conda_channel_alias": "namespacechannelalias",
    }
    api.set_kvstore_key_values(db, "setting/test_namespace_two", namespace_two_settings)

    # setup test environment settings
    environment_settings =  {
        "conda_channel_alias": "envchannelalias",
        "conda_default_packages": ["numpy"]
    }
    api.set_kvstore_key_values(db, "setting/test_namespace/test_env", environment_settings)

    return Settings(
        db=db, deployment_default=default_settings
    )


def test_get_settings_default(settings: Settings):
    test_settings = settings.get_settings()
    
    # ensure that we get the deployment default values
    assert test_settings.default_gid == 999

    # ensure we get the settings overridden by the global settings
    assert test_settings.default_uid == 888
    assert test_settings.conda_channel_alias == "globalchannelalias"
    assert test_settings.conda_command == "myglobalcondacommand"

    # ensure that we get the default value for unset settings
    assert test_settings.default_namespace == "default"


def test_get_settings_namespace(settings: Settings):
    test_settings = settings.get_settings(namespace="test_namespace")
    
    # ensure that we get the deployment default values
    assert test_settings.default_gid == 999

    # ensure that we get the global defaults
    assert test_settings.default_uid == 888

    # ensure we get the settings overridden by the namespace settings
    assert test_settings.conda_channel_alias == "namespacechannelalias"
    assert test_settings.conda_command == "mynamespacecondacommand"
    assert test_settings.conda_default_packages == ["ipykernel"]

    # ensure that we get the default value for unset settings
    assert test_settings.default_namespace == "default"


def test_get_settings_namespace_two(settings: Settings):
    test_settings = settings.get_settings(namespace="test_namespace_two")
    
    # ensure that we get the deployment default values
    assert test_settings.default_gid == 999

    # ensure that we get the global defaults
    assert test_settings.default_uid == 888

    # ensure we get the settings overridden by the namespace settings
    assert test_settings.conda_channel_alias == "namespacechannelalias"
    assert test_settings.conda_command == "myglobalcondacommand"
    assert test_settings.conda_default_packages == []

    # ensure that we get the default value for unset settings
    assert test_settings.default_namespace == "default"


def test_get_settings_environment(settings: Settings):
    test_settings = settings.get_settings(namespace="test_namespace", environment_name="test_env")
    
    # ensure that we get the deployment default values
    assert test_settings.default_gid == 999

    # ensure that we get the global defaults
    assert test_settings.default_uid == 888

    # ensure we get the settings overridden by the environment settings
    assert test_settings.conda_channel_alias == "envchannelalias"
    assert test_settings.conda_command == "mynamespacecondacommand"
    assert test_settings.conda_default_packages == ["numpy"]

    # ensure that we get the default value for unset settings
    assert test_settings.default_namespace == "default"


def test_get_settings_namespace_dne(settings: Settings):
    # get settings for namespace that does not exist - we should
    # still get the default settings
    test_settings = settings.get_settings(namespace="idontexist")
    
    # ensure that we get the deployment default values
    assert test_settings.default_gid == 999

    # ensure we get the settings overridden by the global settings
    assert test_settings.default_uid == 888
    assert test_settings.conda_command == "myglobalcondacommand"


def test_set_settings_global_default(settings: Settings):
    # set test settings
    settings.set_settings(data={"default_uid": 0})

    # ensure the setting is persisted to the right level
    check_settings = settings.get_settings()
    assert check_settings.default_uid == 0
    check_settings = settings.get_settings(namespace="test_namespace")
    assert check_settings.default_uid == 0

def test_set_settings_global_overriden_by_default(settings: Settings):
    # set test settings
    settings.set_settings(data={"conda_channel_alias": "newchanelalias"})

    # ensure the setting is persisted to the right level
    check_settings = settings.get_settings()
    assert check_settings.conda_channel_alias == "newchanelalias"
    check_settings = settings.get_settings(namespace="test_namespace")
    assert check_settings.conda_channel_alias == "namespacechannelalias"


def test_set_settings_invalid_setting_field(settings: Settings):
    with pytest.raises(ValueError, match=r"Invalid setting keys"):
        settings.set_settings(data={"idontexist": "sure", "conda_channel_alias": "mynewalias"})


def test_set_settings_invalid_setting_type(settings: Settings):
    with pytest.raises(ValueError, match=r"Invalid parsing of setting"):
        settings.set_settings(data={"conda_channel_alias": [1,2,3]})


def test_set_settings_invalid_level(settings: Settings):
    with pytest.raises(ValueError, match=r"is a global setting cannot be set within namespace"):
        settings.set_settings(
            namespace="mynamespace", data={"default_uid": 777}
        )
