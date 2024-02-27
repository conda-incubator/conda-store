from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("conda-store")
except PackageNotFoundError:
    # package is not installed
    pass
