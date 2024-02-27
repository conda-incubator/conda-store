from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("conda_store")
except PackageNotFoundError:
    # package is not installed
    pass
