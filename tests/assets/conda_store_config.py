import logging

from conda_store_server.storage import S3Storage
from conda_store_server.server.auth import DummyAuthentication

# ==================================
#      conda-store settings
# ==================================
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/var/lib/conda-store/"
c.CondaStore.environment_directory = "/opt/conda-store/envs/"
# c.CondaStore.database_url = "mysql+pymysql://admin:password@mysql/conda-store"
c.CondaStore.database_url = "postgresql+psycopg2://postgres:password@postgres/conda-store"
c.CondaStore.redis_url = "redis://:password@redis:6379/0"
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 1000
c.CondaStore.default_permissions = "775"
c.CondaStore.conda_included_packages = [
    'ipykernel'
]

c.CondaStore.pypi_included_packages = [
    'nothing'
]


c.S3Storage.internal_endpoint = "minio:9000"
c.S3Storage.external_endpoint = "localhost:9000"
c.S3Storage.access_key = "admin"
c.S3Storage.secret_key = "password"
c.S3Storage.region = "us-east-1"  # minio region default
c.S3Storage.bucket_name = "conda-store"
c.S3Storage.internal_secure = False
c.S3Storage.external_secure = False

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


# ==================================
#         auth settings
# ==================================
c.CondaStoreServer.authentication_class = DummyAuthentication
c.CondaStoreServer.template_vars = {
    "banner": '<div class="alert alert-danger" role="alert">This is a localhost server</div>',
    "logo": "https://quansight.com/_next/image?url=https%3A%2F%2Fa.storyblok.com%2Ff%2F147759%2F1076x520%2Fe6cd6af012%2Fquansight-logo-no-tagline.png&w=3840&q=75",
}

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/environments"]
c.CondaStoreWorker.concurrency = 4
