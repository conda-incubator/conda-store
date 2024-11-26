# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

# Custom hook to build conda-store-server with a local or released version of conda-store-ui.
# To build with a released version of conda-store-ui: make sure to set the CONDA_STORE_UI_VERSION to a valid release
# version in npm.
# Then run `hatch build` to build conda-store-server with the specified version of conda-store-ui.
# To build with a local version of conda-store-ui: set the LOCAL_UI environment variable to the path of the local conda-store-ui directory.
# For example: export LOCAL_UI=<local path for conda-store-ui>  && hatch build --clean

import os
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

CONDA_STORE_UI_VERSION = "2024.11.1"
CONDA_STORE_UI_URL = f"https://registry.npmjs.org/@conda-store/conda-store-ui/-/conda-store-ui-{CONDA_STORE_UI_VERSION}.tgz"

UI_FILES_EXTENSIONS = ["*.js", "*.css", "*.js.map", "*.css.map", "*.html"]

SERVER_DIR = Path("conda_store_server/_internal/server")
SERVER_UI_ASSETS = SERVER_DIR / "static/conda-store-ui"
# FastAPI templates directory
SERVER_UI_TEMPLATES = SERVER_DIR / "templates"


# Note we do not modify the main.js file directly anymore. Instead we leverage
# the use of runtime configuration through condaStoreConfig per
# https://conda.store/conda-store-ui/how-tos/configure-ui
# which is set up in conda-store-server/conda_store_server/_internal/server/templates/conda-store-ui.html
class DownloadCondaStoreUIHook(BuildHookInterface):
    def clean(self, versions: List[str]) -> None:
        """Delete previously vendored UI files. This is called from:
        `hatch clean` and `hatch build --clean`

        Args:
            versions (List[str]): a list of published versions in npm
        """
        super().clean(versions)
        server_build_static_assets = Path(self.root) / SERVER_UI_ASSETS
        shutil.rmtree(server_build_static_assets, ignore_errors=True)

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """UI vendoring within conda-store-server. This can be used to build conda-store-server with a local or
        released version of conda-store-ui (should be available in npm).
        This hook ensures we have the UI files in the correct location for the server to serve them and updates the
        HTML templates to point to the right paths for the UI assets.

        Args:
            version (str): ui version to vendor
        """
        super().initialize(version, build_data)

        if "LOCAL_UI" in os.environ:
            print(
                f"Building with a local version of conda-store-ui located in {os.getenv('LOCAL_UI')}"
            )

            if Path(os.getenv("LOCAL_UI")).exists():
                local_ui_path = os.getenv("LOCAL_UI")
                source_directory = Path(local_ui_path) / "dist"
                if source_directory.exists():
                    self.copy_ui_files(source_directory)
                else:
                    print(f"Directory does not exist: {source_directory}")

            else:
                raise FileNotFoundError(
                    f"Local UI directory {os.getenv('LOCAL_UI')} does not exist"
                )
        # build with a released version of conda-store-ui - this is what we do for conda-store-server releases
        else:
            print(f"Building with conda-store-ui version {CONDA_STORE_UI_VERSION}")
            self.get_ui_release(CONDA_STORE_UI_VERSION)

    def get_ui_release(self, ui_version: str) -> None:
        """Download a released version of conda-store-ui and add it to the
        server's static assets directory.

        Args:
            ui_version (str): conda-store-ui version to download, must be a
            valid npm release
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            tmp_filename = tmp_dir / "conda-store-ui.tgz"

            print(f"Downloading @conda-store/conda-store-ui={CONDA_STORE_UI_VERSION}")
            with urllib.request.urlopen(CONDA_STORE_UI_URL) as response:
                with tmp_filename.open("wb") as f:
                    f.write(response.read())

            print(f"Extracting @conda-store/conda-store-ui={CONDA_STORE_UI_VERSION}")
            with tarfile.open(tmp_filename, "r:gz") as tar:
                tar.extractall(path=tmp_dir)

            source_directory = tmp_dir / "package/dist"

            self.copy_ui_files(source_directory)

    def copy_ui_files(self, source_directory: str) -> None:
        """Copy conda-store-ui files to the conda-server static assets
        directory (SERVER_UI_ASSETS).

        Args:
            source_directory (str): path to the directory containing the UI files
        """
        server_build_static_assets = Path(self.root) / SERVER_UI_ASSETS
        server_build_static_assets.mkdir(parents=True, exist_ok=True)

        print(f"Copying conda-store-ui files from {source_directory} \n")

        try:
            for extension in UI_FILES_EXTENSIONS:
                for file_path in source_directory.glob(extension):
                    target_path = server_build_static_assets / file_path.name
                    # in case the file already exists, remove it
                    if target_path.exists():
                        target_path.unlink()
                    shutil.copy(file_path, target_path)

            print(
                f"Copied files: {[p.name for p in server_build_static_assets.glob('*')]}"
            )

        except OSError as e:
            print(f"Error copying files: {e}")
            raise
