import logging

from conda_store_server.storage import S3Storage

# ==================================
#      conda-store settings
# ==================================
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/var/lib/conda-store/"
c.CondaStore.environment_directory = "/opt/conda-store/envs/"
# c.CondaStore.database_raw_url = "postgresql+psycopg2://admin:password@postgres/conda-store"
c.CondaStore.database_backend = "postgresql+psycopg2"
c.CondaStore.database_username = "admin"
c.CondaStore.database_password = "password"
c.CondaStore.database_host = "postgres"
c.CondaStore.database_port = 5432
c.CondaStore.database_path = "conda-store"
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 100
c.CondaStore.default_permissions = "775"

c.S3Storage.internal_endpoint = "minio:9000"
c.S3Storage.external_endpoint = "localhost:9000"
c.S3Storage.access_key = "admin"
c.S3Storage.secret_key = "password"
c.S3Storage.region = "us-east-1"  # minio region default
c.S3Storage.bucket_name = "conda-store"
c.S3Storage.secure = False

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

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.storage_threshold = 5 * (2 ** 30)  # 5 GB
c.CondaStoreWorker.poll_interval = 10
c.CondaStoreWorker.watch_paths = ["/opt/environments"]
