import os

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
        self.bucket_name = os.environ['S3_BUCKET_NAME']
        self.client = minio.Minio(self.endpoint, os.environ['S3_ACCESS_KEY'], os.environ['S3_SECRET_KEY'], secure=False)

    def fset(self, key, filename):
        self.client.fput_object(self.bucket_name, key, filename)

    def set(self, key, value):
        self.client.put_object(self.bucket_name, key, value)

    def get_url(self, key):
        return self.client.presigned_get_object(self.bucket_name, key)


class LocalStorage(Storage):
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def fset(self, key, value):
