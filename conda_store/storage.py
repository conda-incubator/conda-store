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
        self.endpoint = os.environ['S3_ENDPOINT']
        self.bucket_name = os.environ.get('S3_BUCKET_NAME', 'conda-store')
        self.client = minio.Minio(self.endpoint, os.environ['S3_ACCESS_KEY'], os.environ['S3_SECRET_KEY'], secure=False)

    def fset(self, key, filename):
        self.client.fput_object(self.bucket_name, key, filename)

    def set(self, key, value):
        self.client.put_object(self.bucket_name, key, value)

    def get_url(self, key):
        return self.client.presigned_get_object(self.bucket_name, key)


class LocalStorage(Storage):
    def __init__(self, storage_path, base_url):
        self.storage_path = pathlib.Path(storage_path)
        self.base_url = base_url

    def fset(self, key, filename):
        shutil.copyfile(filename, self.storage_path / key)

    def set(self, key, value):
        with (self.storage_path / key).open('wb') as f:
            f.write(value)

    def get_url(self, key):
        return os.path.join(self.base_url, key)
