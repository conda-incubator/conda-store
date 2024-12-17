# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from typing import Any, Dict

from sqlalchemy.orm import Session
import pydantic

from conda_store_server import api
from conda_store_server._internal import schema


class Settings:
    def __init__(self, db: Session, deployment_default: schema.Settings):
        self.db = db
        self.deployment_default = deployment_default.model_dump()

    def set_settings(
        self,
        namespace: str = None,
        environment_name: str = None,
        data: Dict[str, Any] = {},
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
                    f"Setting {key} is a global setting cannot be set within namespace or environment"
                )

            try:
                validator = pydantic.TypeAdapter(field.annotation)
                validator.validate_python(value)
            except Exception as e:
                raise ValueError(
                    f"Invalid parsing of setting {key} expected type {field.annotation} ran into error {e}"
                )

        if namespace is not None and environment_name is not None:
            prefix = f"setting/{namespace}/{environment_name}"
        elif namespace is not None:
            prefix = f"setting/{namespace}"
        else:
            prefix = "setting"

        api.set_kvstore_key_values(self.db, prefix, data)

    def get_settings(
        self, namespace: str = None, environment_name: str = None
    ) -> schema.Settings:
        """Get full schema.settings object for a given level of specificity.
        If no namespace or environment is given, then the default settings
        are returned. Settings merged follow the merge rules for updating
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
        # bulid list of prefixes to check from least precidence to highest precedence
        prefixes = ["setting"]
        if namespace is not None:
            prefixes.append(f"setting/{namespace}")
        if namespace is not None and environment_name is not None:
            prefixes.append(f"setting/{namespace}/{environment_name}")

        # start building settings with the least specific defaults
        settings = self.deployment_default
        for prefix in prefixes:
            settings.update(api.get_kvstore_key_values(self.db, prefix))

        return schema.Settings(**settings)
