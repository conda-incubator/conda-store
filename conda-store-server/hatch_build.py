from typing import Any, List, Dict
import tempfile
import tarfile
import pathlib
import urllib.request
import shutil

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


CONDA_STORE_UI_VERSION = "0.1.4"
CONDA_STORE_UI_URL = f"https://registry.npmjs.org/@conda-store/conda-store-ui/-/conda-store-ui-{CONDA_STORE_UI_VERSION}.tgz"
CONDA_STORE_UI_FILES = [
    "main.js",
    "main.css",
    "main.css.map",
    "main.js.map",
    "index.html",
]


class DownloadCondaStoreUIHook(BuildHookInterface):
    def clean(self, versions: List[str]) -> None:
        super().clean(versions)
        destination_directory = (
            pathlib.Path(self.root) / "conda_store_server/server/static/conda-store-ui"
        )
        shutil.rmtree(destination_directory, ignore_errors=True)

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        super().initialize(version, build_data)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = pathlib.Path(tmp_dir)
            tmp_filename = tmp_dir / "conda-store-ui.tgz"

            print(f"Downloading @conda-store/conda-store-ui={CONDA_STORE_UI_VERSION}")
            with urllib.request.urlopen(CONDA_STORE_UI_URL) as response:
                with tmp_filename.open("wb") as f:
                    f.write(response.read())

            print(f"Extracting @conda-store/conda-store-ui={CONDA_STORE_UI_VERSION}")
            with tarfile.open(tmp_filename, "r:gz") as tar:
                tar.extractall(path=tmp_dir)

            source_directory = tmp_dir / "package/dist"
            destination_directory = (
                pathlib.Path(self.root)
                / "conda_store_server/server/static/conda-store-ui"
            )
            destination_directory.mkdir(parents=True, exist_ok=True)

            print(f"Copying files {CONDA_STORE_UI_FILES}")
            for filename in CONDA_STORE_UI_FILES:
                shutil.copy(
                    source_directory / filename,
                    destination_directory / filename,
                )
