import pathlib
import re
import shutil
import tarfile
import tempfile
import urllib.request

from pathlib import Path
from typing import Any, Dict, List

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


CONDA_STORE_UI_VERSION = "2024.6.1"
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
        """Quick utility method to remove any straggling ui files from previous versions

        Args:
            versions (List[str]): a list of published versions in npm
        """
        super().clean(versions)
        destination_directory = (
            pathlib.Path(self.root)
            / "conda_store_server/_internal/server/static/conda-store-ui"
        )
        shutil.rmtree(destination_directory, ignore_errors=True)

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """UI vendoring within conda-store-server, right now it downloads the
        published UI, copies the distributed html, js and css files and
        does some on the fly env vars injection.

        Args:
            version (str): ui version to vendor
        """
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
                / "conda_store_server/_internal/server/static/conda-store-ui"
            )
            destination_directory.mkdir(parents=True, exist_ok=True)

            print(
                f"Copying conda-store-ui {CONDA_STORE_UI_FILES} to {destination_directory}"
            )
            for filename in CONDA_STORE_UI_FILES:
                shutil.copy(
                    source_directory / filename,
                    destination_directory / filename,
                )

            # dirty modifications (bound to break eventually!) to
            # main.js to enable easy configuration see
            # conda_store_server/_internal/server/templates/conda-store-ui.html
            # for global variable set
            with (source_directory / "main.js").open("r", encoding="utf-8") as source_f:
                content = source_f.read()
                content = re.sub(
                    '"MISSING_ENV_VAR"', "GLOBAL_CONDA_STORE_STATE", content
                )
                with (destination_directory / "main.js").open(
                    "w", encoding="utf-8"
                ) as dest_f:
                    dest_f.write(content)
            # Add vendoring string to files
            for filename in CONDA_STORE_UI_FILES:
                annotate_vendored(destination_directory / filename)


def annotate_vendored(file_path: str):
    """Auxiliary method to add a vendoring string to the top of a file.
    This helps with tracking the version of the vendored file and the conda-store
    version for which we bundled the artefacts.

    Args:
        file_path (str): conda-store-ui file path
    """
    comment_string = {
        ".js": ["//", ""],
        ".map": ["//", ""],
        ".css": ["/*", "*/"],
        ".html": ["<!--", "-->"],
    }

    vendoring_string = (
        f"{(comment_string.get(Path(file_path).suffix)[0])} "
        f"conda-store-ui version: {CONDA_STORE_UI_VERSION} "
        f"{(comment_string.get(Path(file_path).suffix)[1])} \n"
    )

    with open(file_path, "r") as file:
        raw_content = file.read()

    modified_content = vendoring_string + raw_content

    # Write the modified content back to the file
    with open(file_path, "w") as file:
        file.write(modified_content)
