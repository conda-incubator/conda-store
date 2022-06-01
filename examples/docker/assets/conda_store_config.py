import logging

from conda_store_server.storage import S3Storage
from conda_store_server.server.auth import JupyterHubOAuthAuthentication

# ==================================
#      conda-store settings
# ==================================
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/opt/conda-store/conda-store"
# Also edit `conda-store-server/alembic.ini` accordingly for key sqlalchemy.url
c.CondaStore.database_url = "postgresql+psycopg2://postgres:password@postgres/conda-store"
c.CondaStore.redis_url = "redis://:password@redis:6379/0"
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 100
c.CondaStore.default_permissions = "775"
c.CondaStore.conda_included_packages = [
    "ipykernel"
]

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
c.CondaStoreServer.port = 5000
# This MUST start with `/`
c.CondaStoreServer.url_prefix = "/conda-store"
c.CondaStoreServer.behind_proxy = True


# ==================================
#         auth settings
# ==================================
c.CondaStoreServer.authentication_class = JupyterHubOAuthAuthentication
c.JupyterHubOAuthAuthentication.jupyterhub_url = "https://conda-store.localhost"
c.JupyterHubOAuthAuthentication.client_id = "service-this-is-a-jupyterhub-client"
c.JupyterHubOAuthAuthentication.client_secret = "this-is-a-jupyterhub-secret"
c.JupyterHubOAuthAuthentication.tls_verify = False

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/conda-store/environments/"]
c.CondaStoreWorker.concurrency = 4

# For local dev, make it so that anybody can access any endpoint
c.RBACAuthorizationBackend.unauthenticated_role_bindings = {
    "*/*": {"admin"},
}
