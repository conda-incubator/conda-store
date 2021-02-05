import os


class RegistryStorageBase:
    def __init__(self, conda_store):
        self.storage_directory = conda_store / 'registry'

        (self.storage_directory / 'blobs').mkdir(
            parents=True, exist_ok=True)
        (self.storage_directory / 'manifests').mkdir(
            parents=True, exist_ok=True)

    def exists(self, image, tag):
        path = self.store_directory / 'manifests' / image / tag
        return path.is_file()

    def add_image(self, image):
        pass

    def get_image_tags(self, image):
        path = self.storage_directory / 'manifests' / image
        return os.listdir(path)

    def get_image_manifest(self, image, tag):
        path = self.storage_directory / 'manifests' / image / tag
        with path.open('rb') as f:
            return f.read()

    def get_image_blob(self, image, tag, blob):
        path = self.storage_directory / 'blobs' / blob
        with path.open('rb') as f:
            return f.read()


class RegistryStorageMirror:
    def __init__(self, conda_store):
        super().__init__(self)
