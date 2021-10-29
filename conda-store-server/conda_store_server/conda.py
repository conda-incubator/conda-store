import json
import subprocess
import bz2
import datetime
import yarl

import requests


def normalize_channel_name(channel_alias, channel):
    if channel.startswith("http"):
        return channel

    channel_alias = yarl.URL(channel_alias)
    return str(channel_alias / channel)


def conda_list(prefix, executable: str = "conda"):
    args = [executable, "list", "-p", prefix, "--json"]
    return json.loads(subprocess.check_output(args))


def conda_pack(prefix, output):
    import conda_pack

    conda_pack.pack(prefix=str(prefix), output=str(output))


def download_repodata(
    channel: str, last_update: datetime.datetime = None, architectures=None
):
    """Download repodata for channel only if changed since last update

    A channel consists of several architectures: linux-32, linux-64,
    linux-aarch64, linux-armv6l, linux-armv7l, linux-ppc64le, noarch,
    osx-64, win-32, win-64, zos-z (possibly others).

    Check ``conda.base.constants.KNOWN_SUBDIRS`` for the full list.
    """
    architectures = set(architectures or [conda_platform(), "noarch"])
    channel_url = yarl.URL(channel)

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
        return {}
    response.raise_for_status()

    repodata = response.json()
    if not (architectures <= set(repodata["subdirs"])):
        raise ValueError("required architectures from channel not available")

    repodata["architectures"] = {}
    for architecture in architectures:
        response = requests.get(channel_url / architecture / "repodata.json.bz2")
        response.raise_for_status()
        repodata["architectures"][architecture] = json.loads(
            bz2.decompress(response.content)
        )

    return repodata


def conda_platform():
    """
    Return the platform (in ``conda`` style) the server is running on.

    It will be one of the values in ``conda.base.constants.KNOWN_SUBDIRS``.
    """
    from conda.base.context import context

    return context.subdir
