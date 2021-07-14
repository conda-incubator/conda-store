import json
import subprocess
import logging
import bz2

import requests


logger = logging.getLogger(__name__)


def normalize_channel_name(channel):
    if channel.startswith("http"):
        return channel
    return f"https://conda.anaconda.org/{channel}"


def conda_list(prefix):
    args = ["conda", "list", "-p", prefix, "--json"]
    return json.loads(subprocess.check_output(args))


def conda_pack(prefix, output):
    import os
    import conda_pack

    ignore = os.environ.get("CONDA_PACK_IGNORE_MISSING_FILES", "") == "1"
    conda_pack.pack(
        prefix=str(prefix), output=str(output), ignore_missing_files=ignore,
    )


def download_repodata(channel, architectures=None):
    """Download repodata for channel

    A channel consists of several architectures: linux-32, linux-64,
    linux-aarch64, linux-armv6l, linux-armv7l, linux-ppc64le, noarch,
    osx-64, win-32, win-64, zos-z (possibly others).

    Check ``conda.base.constants.KNOWN_SUBDIRS`` for the full list.
    """
    architectures = set(architectures or [conda_platform(), "noarch"])

    url = f"{channel}/channeldata.json"
    logger.info(f"downloading channeldata url={url}")
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    if not (architectures <= set(data["subdirs"])):
        raise ValueError("required architectures from channel not available")

    repodata = {}
    for architecture in architectures:
        url = f"{channel}/{architecture}/repodata.json.bz2"
        logger.info(f"downloading repodata url={url}")
        resp = requests.get(url)
        resp.raise_for_status()
        repodata[architecture] = json.loads(bz2.decompress(resp.content))

    return repodata


def conda_platform():
    """
    Return the platform (in ``conda`` style) the server is running on.

    It will be one of the values in ``conda.base.constants.KNOWN_SUBDIRS``.
    """
    from conda.base.context import context

    return context.subdir
