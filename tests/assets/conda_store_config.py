# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging

from conda_store_server.server.auth import DummyAuthentication
from conda_store_server.storage import S3Storage


# ==================================
#      conda-store settings
# ==================================
# The default storage_threshold limit was reached on CI, which caused test
# failures
c.CondaStore.storage_threshold = 1024**3
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/var/lib/conda-store/"
c.CondaStore.environment_directory = "/opt/conda-store/envs/{namespace}-{name}"
# c.CondaStore.database_url = "mysql+pymysql://admin:password@mysql/conda-store"
c.CondaStore.database_url = (
    "postgresql+psycopg2://postgres:password@postgres/conda-store"
)
c.CondaStore.redis_url = "redis://:password@redis:6379/0"
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 1000
c.CondaStore.default_permissions = "775"
c.CondaStore.conda_included_packages = ["ipykernel"]

c.CondaStore.pypi_included_packages = ["nothing"]


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
c.CondaStoreServer.port = 8080
# This MUST start with `/`
c.CondaStoreServer.url_prefix = "/conda-store"


# ==================================
#         auth settings
# ==================================
c.CondaStoreServer.authentication_class = DummyAuthentication
c.CondaStoreServer.template_vars = {
    "banner": '<div class="alert alert-danger" role="alert">This is a localhost server</div>',
    "logo": "https://raw.githubusercontent.com/conda-incubator/conda-store/main/docusaurus-docs/community/assets/logos/conda-store-logo-horizontal-lockup.svg",
}

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/environments"]
c.CondaStoreWorker.concurrency = 4

# ==================================
#         registry settings
# ==================================
# from python_docker.registry import Registry
# import os

# def _configure_docker_registry(registry_url: str):
#     return Registry(
#         "https://registry-1.docker.io",
#         username=os.environ.get('DOCKER_USERNAME'),
#         password=os.environ.get('DOCKER_PASSWORD'))

# c.ContainerRegistry.container_registries = {
#     'https://registry-1.docker.io': _configure_docker_registry
# }
