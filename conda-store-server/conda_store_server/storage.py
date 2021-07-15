import io
import os
import shutil

import minio
from traitlets.config import LoggingConfigurable
from traitlets import Unicode, Bool


class Storage(LoggingConfigurable):
    def fset(self, key, filename):
        raise NotImplementedError()

    def set(self, key, value):
        raise NotImplementedError()

    def get_url(self, key):
        raise NotImplementedError()


class S3Storage(Storage):
    internal_endpoint = Unicode(
        help="internal endpoint to reach s3 bucket e.g. 'minio:9000'",
        config=True,
    )

    external_endpoint = Unicode(
        help="internal endpoint to reach s3 bucket e.g. 'localhost:9000'",
        config=True,
    )

    access_key = Unicode(
        help="access key for S3 bucket",
        config=True,
    )

    secret_key = Unicode(
        help="secret key for S3 bucket",
        config=True,
    )

    region = Unicode(
        "us-east-1",
        help="region for s3 bucket",
        config=True,
    )

    bucket_name = Unicode(
        "conda-store",
        help="bucket name for s3 bucket",
        config=True,
    )

    secure = Bool(
        True,
        help="use secure connection to collect to s3 bucket",
        config=True,
    )

    @property
    def internal_client(self):
        if hasattr(self, "_internal_client"):
            return self._internal_client

        self.log.info(
            f"setting up internal client endpoint={self.internal_endpoint} region={self.region} secure={self.secure}"
        )
        self._internal_client = minio.Minio(
            self.internal_endpoint,
            self.access_key,
            self.secret_key,
            region=self.region,
            secure=self.secure,
        )
        self._check_bucket_exists()
        return self._internal_client

    @property
    def external_client(self):
        if hasattr(self, "_external_client"):
            return self._external_client

        self.log.info(
            f"setting up external client endpoint={self.external_endpoint} region={self.region} secure={self.secure}"
        )
        self._external_client = minio.Minio(
            self.external_endpoint,
            self.access_key,
            self.secret_key,
            region=self.region,
            secure=self.secure,
        )
        return self._external_client

    def _check_bucket_exists(self):
        if not self._internal_client.bucket_exists(self.bucket_name):
            raise ValueError(f"S3 bucket={self.bucket_name} does not exist")

    def fset(self, key, filename, content_type="application/octet-stream"):
        self.internal_client.fput_object(
            self.bucket_name, key, filename, content_type=content_type
        )

    def set(self, key, value, content_type="application/octet-stream"):
        self.internal_client.put_object(
            self.bucket_name,
            key,
            io.BytesIO(value),
            length=len(value),
            content_type=content_type,
        )

    def get_url(self, key):
        return self.external_client.presigned_get_object(self.bucket_name, key)


class LocalStorage(Storage):
    storage_path = Unicode(
        "conda-store-state/storage",
        help="directory to store binary blobs of conda-store artifacts",
        config=True,
    )

    storage_url = Unicode(
        help="unauthenticated url where artifacts in storage path are being served from",
        config=True,
    )

    def fset(self, key, filename, content_type=None):
        filename = os.path.join(self.storage_path, key)
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        shutil.copyfile(filename, os.path.join(self.storage_path, key))

    def set(self, key, value, content_type=None):
        filename = os.path.join(self.storage_path, key)
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "wb") as f:
            f.write(value)

    def get_url(self, key):
        return os.path.join(self.storage_url, key)
