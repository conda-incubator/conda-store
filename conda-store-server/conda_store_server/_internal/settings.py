# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import functools
from typing import Any, Callable, Dict

import pydantic
from sqlalchemy.orm import Session

from conda_store_server import api
from conda_store_server._internal import schema


class Settings:
    def __init__(self, db: Session, deployment_default: schema.Settings):
        self.db = db
        self.deployment_default = deployment_default.model_dump()

    def _ensure_closed_session(func: Callable):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.db.close()
            return result

        return wrapper

    @_ensure_closed_session
    def set_settings(
        self,
        namespace: str | None = None,
        environment_name: str | None = None,
        data: Dict[str, Any] | None = None,
    ):
        """Persist settings to the database

        Parameters
        ----------
        namespace : str, optional
            namespace to use to retrieve settings
        environment_name : str, optional
            environment to use to retrieve settings
        data : dict
            settings to upsert
        """
        if data is None:
            return

        # if an environment is specified without a namespace, it is not possible to
        # determine which environment the setting should be applied to. Raise an error.
        if namespace is None and environment_name is not None:
            raise ValueError(
                f"Environment {environment_name} is set without a namespace. Please specify a namespace."
            )

        setting_keys = schema.Settings.model_fields.keys()
        if not data.keys() <= setting_keys:
            invalid_keys = data.keys() - setting_keys
            raise ValueError(f"Invalid setting keys {invalid_keys}")

        for key, value in data.items():
            field = schema.Settings.model_fields[key]
            global_setting = field.json_schema_extra["metadata"]["global"]
            if global_setting and (
                namespace is not None or environment_name is not None
            ):
                raise ValueError(
                    f"Setting {key} is a global setting and cannot be set within a namespace or environment"
                )

            validator = pydantic.TypeAdapter(field.annotation)
            validator.validate_python(value)

        if namespace is not None and environment_name is not None:
            prefix = f"setting/{namespace}/{environment_name}"
        elif namespace is not None:
            prefix = f"setting/{namespace}"
        else:
            prefix = "setting"

        api.set_kvstore_key_values(self.db, prefix, data)

    @_ensure_closed_session
    def get_settings(
        self, namespace: str | None = None, environment_name: str | None = None
    ) -> schema.Settings:
        """Get full schema.settings object for a given level of specificity.
        Settings will be merged together from most specific taking precedence
        over least specific. So, if no namespace or environment is given, then
        the default settings are returned.

        Settings merged follow the merge rules for updating
        dict's. So, lists and dict fields are overwritten opposed to merged.

        Parameters
        ----------
        namespace : str, optional
            namespace to use to retrieve settings
        environment_name : str, optional
            environment to use to retrieve settings

        Returns
        -------
        schema.Settings
            merged settings object
        """
        # build default/global settings object
        settings = self.deployment_default
        settings.update(api.get_kvstore_key_values(self.db, "setting"))

        # bulid list of prefixes to check from least precidence to highest precedence
        prefixes = []
        if namespace is not None:
            prefixes.append(f"setting/{namespace}")
        if namespace is not None and environment_name is not None:
            prefixes.append(f"setting/{namespace}/{environment_name}")

        if len(prefixes) > 0:
            # get the fields that scoped globally. These are the keys that will NOT be
            # merged on for namespace and environment prefixes.
            global_fields = [
                k
                for k, v in schema.Settings.model_fields.items()
                if v.json_schema_extra["metadata"]["global"]
            ]
            # start building settings with the least specific defaults
            for prefix in prefixes:
                new_settings = api.get_kvstore_key_values(self.db, prefix)
                # remove any global fields
                new_settings = {
                    k: v for k, v in new_settings.items() if k not in global_fields
                }
                settings.update(new_settings)

        return schema.Settings(**settings)

    @_ensure_closed_session
    def get_setting(
        self,
        key: str,
        namespace: str | None = None,
        environment_name: str | None = None,
    ) -> Any:  # noqa: ANN401
        """Get a given setting at the given level of specificity. Settings
        will be merged together from most specific taking precedence over
        least specific. Will short cut and look up global setting directly
        (where appropriate) even if a namespace/environment is specified.

        Parameters
        ----------
        key : str
            name of the setting to return
        namespace : str, optional
            namespace to use to retrieve settings
        environment_name : str, optional
            environment to use to retrieve settings

        Returns
        -------
        Any
            setting value, merged for the given level of specificity
        """
        field = schema.Settings.model_fields.get(key)
        if field is None:
            return None

        prefixes = ["setting"]
        # if the setting is a global setting, then there is no need
        # to build up a list of prefixes to check
        if field.json_schema_extra["metadata"]["global"] is False:
            if namespace is not None:
                prefixes.append(f"setting/{namespace}")
                if environment_name is not None:
                    prefixes.append(f"setting/{namespace}/{environment_name}")

        # start building settings with the least specific defaults
        result = self.deployment_default.get(key)
        for prefix in prefixes:
            value = api.get_kvstore_key(self.db, prefix, key)
            if value is not None:
                result = value

        return result
