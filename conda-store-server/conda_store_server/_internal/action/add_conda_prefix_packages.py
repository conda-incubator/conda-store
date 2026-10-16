# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import hashlib
import json
import os
import pathlib

from conda.core.prefix_data import PrefixData

from conda_store_server import api
from conda_store_server._internal import action


def package_hashes(record) -> tuple[str, str]:
    """
    Returns the md5 and sha256 of the package file a prefix record was installed from

    """
    # conda-meta records carry the package file's hashes from repodata
    if record.get("md5") and record.get("sha256"):
        return record.md5, record.sha256

    # mamba writes `package_tarball_full_path` with a `.tar.bz2` extension even
    # when it downloaded the `.conda` file, so locate the file by its name
    path = os.path.join(os.path.dirname(record.package_tarball_full_path), record.fn)
    with open(path, "rb") as f:
        content = f.read()
    return hashlib.md5(content).hexdigest(), hashlib.sha256(content).hexdigest()


def list_conda_prefix_packages(conda_prefix: pathlib.Path):
    """
    Returns a list of the packages that exist for a given prefix

    """
    packages = []

    prefix_data = PrefixData(str(conda_prefix))
    prefix_data.load()

    for record in prefix_data.iter_records():
        md5, sha256 = package_hashes(record)
        package = {
            "build": record.build,
            "build_number": record.build_number,
            "constrains": list(record.constrains),
            "depends": list(record.depends),
            "license": record.license,
            "license_family": record.license_family,
            "md5": md5,
            "sha256": sha256,
            "name": record.name,
            "size": getattr(record, "size", 0),
            "subdir": record.subdir,
            "timestamp": record.timestamp,
            "version": record.version,
            "channel_id": record.channel.base_url,
            "summary": None,
            "description": None,
        }

        info_json = os.path.join(record.extracted_package_dir, "info/about.json")
        if os.path.exists(info_json):
            info = json.load(open(info_json))
            package["summary"] = info.get("summary")
            package["description"] = info.get("description")

        packages.append(package)
    return packages


@action.action
def action_add_conda_prefix_packages(
    context,
    db,
    conda_prefix: pathlib.Path,
    build_id: int,
):
    build = api.get_build(db, build_id=build_id)
    packages = list_conda_prefix_packages(conda_prefix)

    for package in packages:
        conda_package_build = api.create_or_ignore_conda_package(db, package)
        if conda_package_build is None:
            continue  # pypi package
        build.package_builds.append(conda_package_build)
        db.commit()
