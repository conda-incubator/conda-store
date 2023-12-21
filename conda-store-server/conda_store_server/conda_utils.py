"""Interface between conda-store and conda

This module provides all the functionality that is required for
executing conda commands
"""

import bz2
import datetime
import json
import pathlib
import subprocess
import tempfile

import requests
import yaml
import yarl


def normalize_channel_name(channel_alias, channel):
    if channel.startswith("http"):
        return channel

    channel_alias = yarl.URL(channel_alias)
    return str(channel_alias / channel)


def conda_list(prefix, executable: str = "conda"):
    args = [executable, "list", "-p", prefix, "--json"]
    return json.loads(subprocess.check_output(args))


def conda_root_package_dir() -> pathlib.Path:
    args = ["conda", "info", "--json"]
    conf = json.loads(subprocess.check_output(args))
    prefix: pathlib.Path = pathlib.Path(conf["pkgs_dirs"][0])
    return prefix


def conda_pack(prefix, output, ignore_missing_files=True):
    from conda_pack import pack

    pack(
        prefix=str(prefix),
        output=str(output),
        ignore_missing_files=ignore_missing_files,
    )


def conda_lock(specification: "CondaSpecification", conda_exe: str = "mamba"):  # noqa
    from conda.models.dist import Dist
    from conda_lock.conda_lock import run_lock

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


def get_channel_url(channel: str) -> yarl.URL:
    # the conda main channel does not have a channeldata.json within
    # the https://conda.anaconda.org/<channel>/channeldata.json
    # so we replace the given url with it's equivalent alias
    channel_replacements = {
        "https://conda.anaconda.org/main/": yarl.URL(
            "https://repo.anaconda.com/pkgs/main"
        )
    }

    # Note: this doesn't use the / operator to append the trailing / character
    # because it's ignored on Windows. Instead, string substitution is used if
    # the / character is not present
    if channel.endswith("/"):
        normalized_channel_url = yarl.URL(channel)
    else:
        normalized_channel_url = yarl.URL(f"{channel}/")

    return channel_replacements.get(str(normalized_channel_url), yarl.URL(channel))


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

    channel_url = get_channel_url(channel)

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


def is_conda_prefix(conda_prefix: pathlib.Path):
    return (conda_prefix / "conda-meta/history").exists()
