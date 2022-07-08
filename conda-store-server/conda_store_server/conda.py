"""Interface between conda-store and conda

This module provides all the functionality that is required for
executing conda commands
"""

import os
import json
import subprocess
import bz2
import datetime
import hashlib
import tempfile
import pathlib

import yaml
import yarl
import requests

from conda_store_server import schema


def normalize_channel_name(channel_alias, channel):
    if channel.startswith("http"):
        return channel

    channel_alias = yarl.URL(channel_alias)
    return str(channel_alias / channel)


def conda_list(prefix, executable: str = "conda"):
    args = [executable, "list", "-p", prefix, "--json"]
    return json.loads(subprocess.check_output(args))


def conda_pack(prefix, output, ignore_missing_files=True):
    from conda_pack import pack

    pack(
        prefix=str(prefix),
        output=str(output),
        ignore_missing_files=ignore_missing_files,
    )


def conda_lock(specification: schema.CondaSpecification, conda_exe: str = "mamba"):
    from conda_lock.conda_lock import run_lock
    from conda.models.dist import Dist

    with tempfile.TemporaryDirectory() as tmpdir:
        environment_path = pathlib.Path(tmpdir) / "environment.yaml"
        lockfile_path = pathlib.Path(tmpdir) / "environment-lock.yaml"

        with environment_path.open("w") as f:
            f.write(specification.json())

        try:
            run_lock(
                environment_files=[environment_path],
                platforms=[conda_platform()],
                lockfile_path=lockfile_path,
                conda_exe=conda_exe,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(e.output)

        with lockfile_path.open() as f:
            lockfile = yaml.safe_load(f)

    conda_packages = []
    pip_packages = []

    for package in lockfile["package"]:
        if package["manager"] == "conda":
            dist = Dist.from_string(package["url"])
            conda_packages.append(
                {
                    "name": dist.name,
                    "build": dist.build,
                    "build_number": dist.build_number,
                    "constrains": None,
                    "depends": [],
                    "license": None,
                    "license_family": None,
                    "size": -1,
                    "subdir": dist.subdir,
                    "timestamp": None,
                    "version": dist.version,
                    "channel_id": dist.base_url,
                    "md5": package["hash"].get("md5"),
                    "sha256": package["hash"].get("sha256", ""),
                    "summary": None,
                    "description": None,
                }
            )
        elif package["manager"] == "pip":
            pip_packages.append(
                {
                    "name": package["name"],
                    "url": package["url"],
                    "version": package["version"],
                    "sha256": package["hash"]["sha256"],
                }
            )

    return {"conda": conda_packages, "pip": pip_packages}


def download_repodata(
    channel: str,
    last_update: datetime.datetime = None,
    subdirs=None,
):
    """Download repodata for channel only if changed since last update

    A channel consists of several architectures: linux-32, linux-64,
    linux-aarch64, linux-armv6l, linux-armv7l, linux-ppc64le, noarch,
    osx-64, win-32, win-64, zos-z (possibly others).

    Check ``conda.base.constants.KNOWN_SUBDIRS`` for the full list.
    """
    subdirs = set(subdirs or [conda_platform(), "noarch"])

    # the conda main channel does not have a channeldata.json within
    # the https://conda.anaconda.org/<channel>/channeldata.json
    # so we replace the given url with it's equivalent alias
    channel_replacements = {
        "https://conda.anaconda.org/main/": yarl.URL(
            "https://repo.anaconda.com/pkgs/main"
        )
    }
    normalized_channel_url = yarl.URL(channel) / "./"
    channel_url = channel_replacements.get(
        str(normalized_channel_url), yarl.URL(channel)
    )

    headers = {}
    if last_update:
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Modified-Since
        # only download channeldata.json if it has been modified since
        # last update to minimize bandwidth usage of channel updates
        # most static web servers obey this header otherwise it will
        # be ignored
        headers["If-Modified-Since"] = last_update.strftime("%a, %d %b %Y %H:%M:%S GMT")

    response = requests.get(channel_url / "channeldata.json", headers=headers)
    if response.status_code == 304:  # 304 Not Modified since last_update
        return {"architectures": {}}
    response.raise_for_status()

    repodata = response.json()
    repodata["architectures"] = {}
    for subdir in subdirs:
        response = requests.get(
            channel_url / subdir / "repodata.json.bz2", headers=headers
        )
        if response.status_code == 304:  # 304 Not Modified since last_update
            continue
        response.raise_for_status()
        repodata["architectures"][subdir] = json.loads(bz2.decompress(response.content))
    return repodata


def conda_platform():
    """
    Return the platform (in ``conda`` style) the server is running on.

    It will be one of the values in ``conda.base.constants.KNOWN_SUBDIRS``.
    """
    from conda.base.context import context

    return context.subdir


def conda_prefix_packages(prefix):
    """
    Returns a list of the packages that exist for a given prefix

    """
    from conda.core.prefix_data import PrefixData

    packages = []

    prefix_data = PrefixData(prefix)
    prefix_data.load()

    for record in prefix_data.iter_records():
        package = {
            "build": record.build,
            "build_number": record.build_number,
            "constrains": list(record.constrains),
            "depends": list(record.depends),
            "license": record.license,
            "license_family": record.license_family,
            "md5": hashlib.md5(
                open(record.package_tarball_full_path, "rb").read()
            ).hexdigest(),
            "sha256": hashlib.sha256(
                open(record.package_tarball_full_path, "rb").read()
            ).hexdigest(),
            "name": record.name,
            "size": record.size,
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
