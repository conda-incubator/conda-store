# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import mock

import pydantic
import pytest

from conda_store_server import api
from conda_store_server._internal import schema
from conda_store_server._internal.settings import Settings


@pytest.fixture
def settings(db) -> Settings:
    default_settings = schema.Settings(
        default_uid=999, default_gid=999, conda_channel_alias="defaultchannelalias"
    )

    # setup test global settings
    global_settings = {
        "default_uid": 888,
        "conda_channel_alias": "globalchannelalias",
        "conda_command": "myglobalcondacommand",
    }
    api.set_kvstore_key_values(db, "setting", global_settings)

    # setup test namespace settings
    namespace_settings = {
        "conda_channel_alias": "namespacechannelalias",
        "conda_command": "mynamespacecondacommand",
        "conda_default_packages": ["ipykernel"],
    }
    api.set_kvstore_key_values(db, "setting/test_namespace", namespace_settings)

    # setup test namespace (two) settings
    namespace_two_settings = {
        "conda_channel_alias": "namespacechannelalias",
    }
    api.set_kvstore_key_values(db, "setting/test_namespace_two", namespace_two_settings)

    # setup test environment settings
    environment_settings = {
        "conda_channel_alias": "envchannelalias",
        "conda_default_packages": ["numpy"],
    }
    api.set_kvstore_key_values(
        db, "setting/test_namespace/test_env", environment_settings
    )

    return Settings(db=db, deployment_default=default_settings)


def test_ensure_session_is_closed(settings: Settings):
    # run a query against the db to start a transaction
    settings.get_settings()
    # ensure that the settings object cleans up it's transaction
    assert not settings.db.in_transaction()


@mock.patch("conda_store_server.api.get_kvstore_key_values")
def test_ensure_session_is_closed_on_error(
    mock_get_kvstore_key_values, settings: Settings
):
    mock_get_kvstore_key_values.side_effect = Exception

    # run a query that will raise an exception
    with pytest.raises(Exception):
        settings.get_settings()

    # ensure that the settings object cleans up it's transaction
    assert not settings.db.in_transaction()


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
    # the "global" metadata setting should be respected. Since `conda_command`
    # is scoped globally, even though we are looking at the "namespace" level,
    # the "global" value should be returned
    assert test_settings.conda_command == "myglobalcondacommand"
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
    test_settings = settings.get_settings(
        namespace="test_namespace", environment_name="test_env"
    )

    # ensure that we get the deployment default values
    assert test_settings.default_gid == 999

    # ensure that we get the global defaults
    assert test_settings.default_uid == 888

    # ensure we get the settings overridden by the environment settings
    assert test_settings.conda_channel_alias == "envchannelalias"
    assert test_settings.conda_command == "myglobalcondacommand"
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
        settings.set_settings(
            data={"idontexist": "sure", "conda_channel_alias": "mynewalias"}
        )


def test_set_settings_invalid_setting_type(settings: Settings):
    with pytest.raises(pydantic.ValidationError):
        settings.set_settings(data={"conda_channel_alias": [1, 2, 3]})


def test_set_settings_invalid_level(settings: Settings):
    with pytest.raises(
        ValueError,
        match="Setting default_uid is a global setting and cannot be set within a namespace or environment",
    ):
        settings.set_settings(namespace="mynamespace", data={"default_uid": 777})


def test_set_settings_environment_without_namespace(settings: Settings):
    with pytest.raises(ValueError, match=r"Please specify a namespace"):
        settings.set_settings(
            environment_name="test_env", data={"conda_channel_alias": "mynewalias"}
        )


def test_get_global_setting(settings: Settings):
    test_setting = settings.get_setting("default_namespace")
    assert test_setting == "default"


def test_get_setting_invalid(settings: Settings):
    test_setting = settings.get_setting("notarealfield")
    assert test_setting is None

    test_setting = settings.get_setting(
        "notarealfield", namespace="test_namespace", environment_name="test_env"
    )
    assert test_setting is None


def test_get_setting_overriden(settings: Settings):
    # conda_channel_alias is not a global command, it may be overriden
    test_setting = settings.get_setting("conda_channel_alias")
    assert test_setting == "globalchannelalias"
    # default_uid is a global setting. It should never be overriden
    test_setting = settings.get_setting("default_uid")
    assert test_setting == 888
    # conda_command is also a global setting. Even if somehow the value gets
    # injected into the db (as in this test setup), get_setting should honour
    # just the global setting
    test_setting = settings.get_setting("conda_command")
    assert test_setting == "myglobalcondacommand"

    test_setting = settings.get_setting(
        "conda_channel_alias", namespace="test_namespace"
    )
    assert test_setting == "namespacechannelalias"
    test_setting = settings.get_setting("default_uid", namespace="test_namespace")
    assert test_setting == 888
    test_setting = settings.get_setting("conda_command", namespace="test_namespace")
    assert test_setting == "myglobalcondacommand"

    test_setting = settings.get_setting(
        "conda_channel_alias", namespace="test_namespace", environment_name="test_env"
    )
    assert test_setting == "envchannelalias"
    test_setting = settings.get_setting(
        "default_uid", namespace="test_namespace", environment_name="test_env"
    )
    assert test_setting == 888
    test_setting = settings.get_setting(
        "conda_command", namespace="test_namespace", environment_name="test_env"
    )
    assert test_setting == "myglobalcondacommand"
