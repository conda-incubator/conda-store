# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging

from conda_store_server.server.auth import JupyterHubOAuthAuthentication
from conda_store_server.storage import S3Storage


# ==================================
#      conda-store settings
# ==================================
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/var/lib/conda-store/"
c.CondaStore.environment_directory = "/opt/conda-store/envs/{namespace}-{name}"
# Also edit `conda-store-server/alembic.ini` accordingly for key sqlalchemy.url
c.CondaStore.database_url = (
    "postgresql+psycopg2://postgres:password@postgres/conda-store"
)
c.CondaStore.upgrade_db = True
c.CondaStore.redis_url = "redis://:password@redis:6379/0"
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 100
c.CondaStore.default_permissions = "775"
c.CondaStore.conda_allowed_channels = [
    "https://repo.anaconda.com/pkgs/main",
    "main",
    "conda-forge",
]
c.CondaStore.conda_included_packages = ["ipykernel"]

c.S3Storage.internal_endpoint = "minio:9000"
c.S3Storage.external_endpoint = "conda-store.localhost:9080"
c.S3Storage.access_key = "admin"
c.S3Storage.secret_key = "password"
c.S3Storage.region = "us-east-1"  # minio region default
c.S3Storage.bucket_name = "conda-store"
c.S3Storage.internal_secure = False
c.S3Storage.external_secure = True

# ==================================
#        server settings
# ==================================
c.CondaStoreServer.log_level = logging.INFO
c.CondaStoreServer.enable_ui = True
c.CondaStoreServer.enable_api = True
c.CondaStoreServer.enable_registry = True
c.CondaStoreServer.enable_metrics = True
c.CondaStoreServer.address = "0.0.0.0"
c.CondaStoreServer.port = 8080
# This MUST start with `/`
c.CondaStoreServer.url_prefix = "/conda-store"
c.CondaStoreServer.behind_proxy = True


# ==================================
#         auth settings
# ==================================
c.CondaStoreServer.authentication_class = JupyterHubOAuthAuthentication
c.JupyterHubOAuthAuthentication.jupyterhub_url = "http://conda-store.localhost"
c.JupyterHubOAuthAuthentication.client_id = "service-this-is-a-jupyterhub-client"
c.JupyterHubOAuthAuthentication.client_secret = "this-is-a-jupyterhub-secret"
c.JupyterHubOAuthAuthentication.oauth_callback_url = "/conda-store/oauth_callback/"
c.JupyterHubOAuthAuthentication.tls_verify = False
c.JupyterHubOAuthAuthentication.access_scope = "conda-store-user"

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/environments/"]
c.CondaStoreWorker.concurrency = 4

# For local dev, make it so that anybody can access any endpoint
c.RBACAuthorizationBackend.unauthenticated_role_bindings = {
    "*/*": {"admin"},
}

c.AuthenticationBackend.predefined_tokens = {
    "this-is-a-jupyterhub-secret-token": {
        "primary_namespace": "default",
        "role_bindings": {
            "*/*": ["admin"],
        },
    }
}
