import os
import shutil
import tarfile
import tempfile
import urllib.request

from pathlib import Path
from typing import Any, Dict, List

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from jinja2 import Environment, FileSystemLoader


CONDA_STORE_UI_VERSION = "2024.3.1"
CONDA_STORE_UI_URL = f"https://registry.npmjs.org/@conda-store/conda-store-ui/-/conda-store-ui-{CONDA_STORE_UI_VERSION}.tgz"
CONDA_STORE_UI_FILES = [
    "main.js",
    "main.css",
    "main.css.map",
    "main.js.map",
    "index.html",
]
UI_FILES_EXTENSIONS = ["*.js", "*.css", "*.map", "*.html"]

SERVER_UI_ASSETS = "conda_store_server/_internal/server/static/conda-store-ui"
SERVER_UI_TEMPLATES = "conda_store_server/_internal/server/static/templates"


# Note we do not modify the main.js file directly anymore. Instead we leverage
# the use of runtime configuration through condaStoreConfig per
# https://conda.store/conda-store-ui/how-tos/configure-ui
# which is set up in conda-store-server/conda_store_server/_internal/server/templates/conda-store-ui.html
class DownloadCondaStoreUIHook(BuildHookInterface):
    def clean(self, versions: List[str]) -> None:
        """Quick utility method to remove any straggling ui files from previous versions

        Args:
            versions (List[str]): a list of published versions in npm
        """
        super().clean(versions)
        server_build_static_assets = Path(self.root) / SERVER_UI_ASSETS
        shutil.rmtree(server_build_static_assets, ignore_errors=True)

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """UI vendoring within conda-store-server, right now it downloads the
        published UI, copies the distributed html, js and css files and
        does some on the fly env vars injection.

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
                self.copy_ui_files(source_directory)

            else:
                raise FileNotFoundError(
                    f"Local UI directory {os.getenv('LOCAL_UI')} does not exist"
                )
        else:
            print(f"Building with conda-store-ui version {CONDA_STORE_UI_VERSION}")
            self.get_ui_release(CONDA_STORE_UI_VERSION)

    def get_ui_release(self, ui_version: str) -> None:
        """Donwload a released version of conda-store-ui and add it to the
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

            # server_build_static_assets = (Path(self.root)/ SERVER_UI_ASSETS)
            # server_build_static_assets.mkdir(parents=True, exist_ok=True)

            # print(f"Copying conda-store-ui {CONDA_STORE_UI_FILES}")
            # for filename in CONDA_STORE_UI_FILES:
            #     shutil.copy(
            #         source_directory / filename,
            #         server_build_static_assets / filename,
            #     )

            self.copy_ui_files(source_directory)

    def copy_ui_files(self, source_directory: str) -> None:
        """Copy a local version of conda-store-ui to the server's static assets
        directory.

        Args:
            local_ui_path (str): path to a local version of conda-store-ui
        """
        # source_directory = Path(local_ui_path)/ "dist"
        server_build_static_assets = Path(self.root) / SERVER_UI_ASSETS
        server_build_static_assets.mkdir(parents=True, exist_ok=True)

        print(f"Copying conda-store-ui files from {source_directory}")

        try:
            for extension in UI_FILES_EXTENSIONS:
                for file_path in source_directory.glob(extension):
                    target_path = server_build_static_assets / file_path.name
                if target_path.exists():
                    target_path.unlink()
                shutil.copy(file_path, target_path)

                # Print all files in the target directory after copying
            print("Copied files:")
            for file in server_build_static_assets.glob("*"):
                print(file.name)
        except (IOError, OSError) as e:
            print(f"Error copying files: {e}")
            raise

    def _update_ui_template():

        # Render the Jinja template - note this is different from the FastAPI templates
        template_dir = Path(SERVER_UI_ASSETS)
        output_dir = Path(SERVER_UI_TEMPLATES)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("conda-store-ui-template.html")

        main_js_file = "static/conda-store-ui/main.8217000e38695a5bf780.js"
        rendered_html = template.render(main_js_file=main_js_file)
        output_path = os.path.join(output_dir, "conda-store-ui.html")
        with open(output_path, "w") as f:
            f.write(rendered_html)

        print(f"Rendered HTML saved to {output_path}")
