# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os

from jupyterhub.auth import DummyAuthenticator
from jupyterhub.spawner import SimpleLocalProcessSpawner


c.JupyterHub.ip = "0.0.0.0"

c.JupyterHub.authenticator_class = DummyAuthenticator
c.DummyAuthenticator.password = "test"

c.Spawner.cmd = ["jupyter-labhub"]


class CondaStoreSpawner(SimpleLocalProcessSpawner):
    # must override spawner to setup the conda-store environment paths
    # properly
    def make_preexec_fn(self, name):
        home = self.home_dir

        func = super().make_preexec_fn(name)

        def preexec():
            func()
            with open(os.path.join(home, ".condarc"), "w") as f:
                f.write(
                    json.dumps(
                        {
                            "envs_dirs": [
                                "/opt/conda-store/conda-store/default/envs",
                                "/opt/conda-store/conda-store/filesystem/envs",
                                f"/opt/conda-store/conda-store/{self.user.name}/envs",
                            ]
                        }
                    )
                )

        return preexec


c.JupyterHub.spawner_class = CondaStoreSpawner

c.JupyterHub.services = [
    {
        "name": "conda-store",
        "oauth_client_id": "service-this-is-a-jupyterhub-client",
        "admin": True,
        "url": "http://conda-store.localhost/conda-store/",
        "api_token": "this-is-a-jupyterhub-secret",
        "oauth_redirect_uri": "/conda-store/oauth_callback/",
        "oauth_no_confirm": True,  # allows no authorize yes/no button
        "oauth_client_allowed_scopes": [
            "self", "inherit", "access:services",
        ]
    }
]

c.JupyterHub.load_roles = [
    {
        "name": "conda-store-user",
        "scopes": [
            "self", 'access:services!service=conda-store',
        ],
        "groups": ["conda-store-user"],
    }
]

c.Authenticator.admin_users = {'admin'}
