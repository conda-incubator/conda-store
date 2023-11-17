from pathlib import Path

__version__ = "2023.10.1"


CONDA_STORE_DIR = Path.home() / ".conda-store"


# Default build_key_version. Must be None here, initialized from the config file
_BUILD_KEY_VERSION = None
