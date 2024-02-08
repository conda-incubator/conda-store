import os
import pathlib
import shutil
import tempfile
import typing

# This import is needed to avoid the following error on conda imports:
# AttributeError: 'Logger' object has no attribute 'trace'
import conda.gateways.logging  # noqa
import conda_package_handling.api
import conda_package_streaming.url
import filelock
from conda.base.constants import PACKAGE_CACHE_MAGIC_FILE
from conda.common.path import expand, strip_pkg_extension
from conda.core.package_cache_data import (
    PackageCacheRecord,
    PackageRecord,
    getsize,
    read_index_json,
    write_as_json_to_file,
)
from conda.gateways.disk.update import touch
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
                # This magic file, which is currently set to "urls.txt", is used
                # to check cache permissions in conda, see _check_writable in
                # PackageCacheData.
                #
                # Sometimes this file is not yet created while this action is
                # running. Without this magic file, PackageCacheData cache
                # query functions, like query_all, will return nothing.
                #
                # If the magic file is not present, this error might be thrown
                # during the lockfile install action:
                #
                # File "/opt/conda/lib/python3.10/site-packages/conda/misc.py", line 110, in explicit
                #   raise AssertionError("No package cache records found")
                #
                # The code below is from create_package_cache_directory in
                # conda, which creates the package cache, but we only need the
                # magic file part here:
                cache_magic_file = pkgs_dir / PACKAGE_CACHE_MAGIC_FILE
                if not cache_magic_file.exists():
                    sudo_safe = expand(pkgs_dir).startswith(expand("~"))
                    touch(cache_magic_file, mkdir=True, sudo_safe=sudo_safe)

                if file_path.exists():
                    context.log.info(f"SKIPPING {filename} | FILE EXISTS\n")
                else:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_dir = pathlib.Path(tmp_dir)
                        file_path = tmp_dir / filename
                        file_path_str = str(file_path)
                        extracted_dir = pathlib.Path(
                            strip_pkg_extension(file_path_str)[0]
                        )
                        extracted_dir_str = str(extracted_dir)
                        context.log.info(f"DOWNLOAD {filename} | {count_message}\n")
                        (
                            filename,
                            conda_package_stream,
                        ) = conda_package_streaming.url.conda_reader_for_url(url)
                        with file_path.open("wb") as f:
                            shutil.copyfileobj(conda_package_stream, f)
                        conda_package_handling.api.extract(
                            file_path_str, dest_dir=extracted_dir
                        )

                        # This code is needed to avoid failures when building in
                        # parallel while using the shared cache.
                        #
                        # Package tarballs contain the info/index.json file,
                        # which is used by conda to create the
                        # info/repodata_record.json file. The latter is used to
                        # interact with the cache. _make_single_record from
                        # PackageCacheData would create the repodata json file
                        # if it's not present, which would happen in conda-store
                        # during the lockfile install action. The repodata file
                        # is not created if it already exists.
                        #
                        # The code that does that in conda is similar to the code
                        # below. However, there is an important difference. The
                        # code in conda would fail to read the url and return None
                        # here:
                        #
                        #   url = self._urls_data.get_url(package_filename)
                        #
                        # And that would result in the channel field of the json
                        # file being set to "<unknown>". This is a problem because
                        # the channel is used when querying cache entries, via
                        # match_individual from MatchSpec, which would always result
                        # in a mismatch because the proper channel value is
                        # different.
                        #
                        # That would make conda think that the package is not
                        # available in the cache, so it would try to download it
                        # outside of this action, where no locking is implemented.
                        #
                        # As of now, conda's cache is not atomic, so the same
                        # dependencies requested by different builds would overwrite
                        # each other causing random failures during the build
                        # process.
                        #
                        # To avoid this problem, the code below does what the code
                        # in conda does but also sets the url properly, which would
                        # make the channel match properly during the query process
                        # later. So no dependencies would be downloaded outside of
                        # this action and cache corruption is prevented.
                        #
                        # To illustrate, here's a diff of an old conda entry, which
                        # didn't work, versus the new one created by this action:
                        #
                        # --- /tmp/old.txt        2024-02-05 01:08:16.879751010 +0100
                        # +++ /tmp/new.txt        2024-02-05 01:08:02.919319887 +0100
                        # @@ -2,7 +2,7 @@
                        #    "arch": "x86_64",
                        #    "build": "conda_forge",
                        #    "build_number": 0,
                        # -  "channel": "<unknown>",
                        # +  "channel": "https://conda.anaconda.org/conda-forge/linux-64",
                        #    "constrains": [],
                        #    "depends": [],
                        #    "features": "",
                        # @@ -15,5 +15,6 @@
                        #    "subdir": "linux-64",
                        #    "timestamp": 1578324546067,
                        #    "track_features": "",
                        # +  "url": "https://conda.anaconda.org/conda-forge/linux-64/_libgcc_mutex-0.1-conda_forge.tar.bz2",
                        #    "version": "0.1"
                        #  }
                        #
                        # Also see the comment above about the cache magic file.
                        # Without the magic file, cache queries would fail even if
                        # repodata_record.json files have proper channels specified.

                        # This file is used to parse cache records via PackageCacheRecord in conda
                        repodata_file = extracted_dir / "info" / "repodata_record.json"

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
                            extracted_package_dir=extracted_dir_str,
                        )

                        repodata_record = PackageRecord.from_objects(
                            package_cache_record
                        )
                        write_as_json_to_file(repodata_file, repodata_record)

                        # This is to ensure _make_single_record in conda never
                        # sees the extracted package directory without our
                        # repodata_record file being there. Otherwise, conda
                        # would attempt to create the repodata file, with the
                        # channel field set to "<unknown>", which would make the
                        # above code pointless. Using symlinks here would be
                        # better since those are atomic on Linux, but I don't
                        # want to create any permanent directories on the
                        # filesystem.
                        shutil.rmtree(pkgs_dir / extracted_dir.name, ignore_errors=True)
                        shutil.move(extracted_dir, pkgs_dir / extracted_dir.name)
                        shutil.move(file_path, pkgs_dir / file_path.name)
