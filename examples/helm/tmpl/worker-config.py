import logging
import os

from conda_store_server.storage import S3Storage

# ==================================
#      conda-store settings
# ==================================
c.CondaStore.storage_threshold = 1024
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/opt/conda-store/conda-store/"
c.CondaStore.database_url = f"postgresql+psycopg2://{os.environ.get('POSTGRES_USERNAME')}:{os.environ.get('POSTGRES_PASSWORD')}@postgres/conda-store"
c.CondaStore.redis_url = (
    f"redis://:{os.environ.get('REDIS_PASSWORD')}@redis:6379/0"
)
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 100
c.CondaStore.default_permissions = "555"
c.CondaStore.conda_included_packages = ["ipykernel"]
c.CondaStore.environment_directory = "{store_directory}/{namespace}/envs/{namespace}-{name}"
c.CondaStore.default_namespace = "global"
c.CondaStore.filesystem_namespace = "conda-store"
c.CondaStore.conda_allowed_channels = []  # allow all channels
c.CondaStore.conda_indexed_channels = [
    "main",
    "conda-forge",
    "https://repo.anaconda.com/pkgs/main",
]

# ==================================
#      s3 settings
# ==================================
c.S3Storage.internal_endpoint = "minio:9000"
c.S3Storage.internal_secure = False
c.S3Storage.external_endpoint = "localhost:9000"
c.S3Storage.external_secure = False
c.S3Storage.access_key = os.environ.get('MINIO_USERNAME')
c.S3Storage.secret_key = os.environ.get('MINIO_PASSWORD')
c.S3Storage.region = "us-east-1"  # minio region default
c.S3Storage.bucket_name = "conda-store"

c.RBACAuthorizationBackend.role_mappings_version = 2

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/environments"]
c.CondaStoreWorker.concurrency = 4
