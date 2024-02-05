import os
import pathlib
import shutil
import typing

# This import is needed to avoid the following error on conda imports:
# AttributeError: 'Logger' object has no attribute 'trace'
import conda.gateways.logging  # noqa
import conda_package_handling.api
import conda_package_streaming.url
import filelock
from conda.core.package_cache_data import (
    PackageCacheRecord,
    PackageRecord,
    getsize,
    read_index_json,
    write_as_json_to_file,
)
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
                file_path_str = str(file_path)
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
                    conda_package_handling.api.extract(file_path_str)

                    # Otherwise .conda, do nothing in that case
                    ext = ".tar.bz2"
                    if file_path_str.endswith(ext):
                        extracted_dir = pathlib.Path(file_path_str.replace(ext, ""))
                        # This file is used to parse cache records via PackageCacheRecord in conda
                        repodata_file = extracted_dir / "info" / "repodata_record.json"
                        index_file = extracted_dir / "info" / "index.json"
                        assert index_file.exists()

                        if not repodata_file.exists():
                            raw_json_record = read_index_json(extracted_dir)
                            fn = os.path.basename(file_path_str)
                            md5 = package["hash"]["md5"]
                            size = getsize(file_path_str)

                            package_cache_record = PackageCacheRecord.from_objects(
                                raw_json_record,
                                url=url,
                                fn=fn,
                                md5=md5,
                                size=size,
                                package_tarball_full_path=file_path_str,
                                extracted_package_dir=str(extracted_dir),
                            )

                            repodata_record = PackageRecord.from_objects(
                                package_cache_record
                            )
                            write_as_json_to_file(repodata_file, repodata_record)
                            assert repodata_file.exists()
