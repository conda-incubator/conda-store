import os
from conda_store_server.storage import S3Storage

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
c.CondaStore.default_namespace = "global"
c.CondaStore.filesystem_namespace = "conda-store"
c.CondaStore.conda_allowed_channels = []  # allow all channels
c.CondaStore.conda_indexed_channels = [
    "main",
    "conda-forge",
    "https://repo.anaconda.com/pkgs/main",
]