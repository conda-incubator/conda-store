import pathlib
import shutil
import typing

import conda_package_handling.api
import conda_package_streaming.url
import filelock
from conda_store_server import action, conda_utils


@action.action
def action_fetch_and_extract_conda_packages(
    context,
    conda_lock_spec: typing.Dict,
    pkgs_dir: pathlib.Path,
    platforms: typing.List[str] = [conda_utils.conda_platform(), "noarch"],
):
    """Download packages from a conda-lock specification using filelocks"""
    packages_searched = 1
    total_packages = len(conda_lock_spec["package"])

    for package in conda_lock_spec["package"]:
        packages_searched += 1
        if package["manager"] == "conda" and package["platform"] in platforms:
            url = package["url"]
            filename = pathlib.Path(url).name
            lock_filename = pkgs_dir / f"{filename}.lock"
            file_path = pkgs_dir / filename
            count_message = f"{packages_searched} of {total_packages}"
            with filelock.FileLock(str(lock_filename)):
                if file_path.exists():
                    context.log.info(f"SKIPPING {filename} | FILE EXISTS\n")
                else:
                    context.log.info(f"DOWNLOAD {filename} | {count_message}\n")
                    (
                        filename,
                        conda_package_stream,
                    ) = conda_package_streaming.url.conda_reader_for_url(url)
                    with file_path.open("wb") as f:
                        shutil.copyfileobj(conda_package_stream, f)
                    conda_package_handling.api.extract(str(file_path))
