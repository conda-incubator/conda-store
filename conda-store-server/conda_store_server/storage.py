import io
import os
import pathlib
import shutil

import minio


class Storage:
    def fset(self, key, filename):
        raise NotImplementedError()

    def set(self, key, value):
        raise NotImplementedError()

    def get_url(self, key):
        raise NotImplementedError()


class S3Storage(Storage):
    def __init__(self):
        self.endpoint = os.environ["CONDA_STORE_S3_ENDPOINT"]
        self.bucket_name = os.environ.get("CONDA_STORE_S3_BUCKET_NAME", "conda-store")
        self.client = minio.Minio(
            self.endpoint,
            os.environ["CONDA_STORE_S3_ACCESS_KEY"],
            os.environ["CONDA_STORE_S3_SECRET_KEY"],
            secure=False,
        )
        self._check_bucket_exists()

    def _check_bucket_exists(self):
        if not self.client.bucket_exists(self.bucket_name):
            raise ValueError(f"S3 bucket={self.bucket_name} does not exist")

    def fset(self, key, filename, content_type="application/octet-stream"):
        self.client.fput_object(
            self.bucket_name, key, filename, content_type=content_type
        )

    def set(self, key, value, content_type="application/octet-stream"):
        self.client.put_object(
            self.bucket_name,
            key,
            io.BytesIO(value),
            length=len(value),
            content_type=content_type,
        )

    def get_url(self, key):
        return self.client.presigned_get_object(self.bucket_name, key)


class LocalStorage(Storage):
    def __init__(self, storage_path, base_url=None):
        self.storage_path = pathlib.Path(storage_path)
        if not self.storage_path.is_dir():
            self.storage_path.mkdir(parents=True)
        self.base_url = base_url

    def fset(self, key, filename, content_type=None):
        shutil.copyfile(filename, self.storage_path / key)

    def set(self, key, value, content_type=None):
        with (self.storage_path / key).open("wb") as f:
            f.write(value)

    def get_url(self, key):
        return os.path.join(self.base_url, key)
