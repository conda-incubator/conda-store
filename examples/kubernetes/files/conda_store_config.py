import logging

from conda_store_server.server.auth import DummyAuthentication
from conda_store_server.storage import S3Storage

# ==================================
#      conda-store settings
# ==================================
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/opt/conda-store/conda-store/"
c.CondaStore.database_url = "postgresql+psycopg2://admin:password@postgres/conda-store"
c.CondaStore.redis_url = "redis://:password@redis:6379/0"
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 100
c.CondaStore.default_permissions = "775"

c.S3Storage.internal_endpoint = "minio:9000"
c.S3Storage.internal_secure = False
c.S3Storage.external_endpoint = "localhost:30900"
c.S3Storage.external_secure = False
c.S3Storage.access_key = "admin"
c.S3Storage.secret_key = "password"
c.S3Storage.region = "us-east-1"  # minio region default
c.S3Storage.bucket_name = "conda-store"

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
c.CondaStoreServer.url_prefix = "/"


# ==================================
#         auth settings
# ==================================
c.CondaStoreServer.authentication_class = DummyAuthentication

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/environments"]
c.CondaStoreWorker.concurrency = 4
