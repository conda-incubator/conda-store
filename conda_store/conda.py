import json
import subprocess
import logging

import requests
from conda_pack import pack

logger = logging.getLogger(__name__)


def conda_list(prefix):
    args = ['conda', 'list', '-p', prefix, '--json']
    return json.loads(subprocess.check_output(args))


def conda_pack(prefix, output):
    pack(prefix=str(prefix), output=str(output))


def conda_docker(prefix, output, image_name, base_image='frolvlad/alpine-glibc:latest'):
    args = [
        'conda', 'docker', 'build',
        '-p', prefix,
        '-o', output,
        '-b', base_image,
        '-i', image_name
    ]
    subprocess.check_output(args)


def download_repodata(channel, architectures=None):
    """Download repodata for channel

    A channel consists of several architectures: linux-32, linux-64,
    linux-aarch64, linux-armv6l, linux-armv7l, linux-ppc64le, noarch,
    osx-64, win-32, win-64, zos-z (possibly others)
    """
    architectures = set(architectures or ['linux-64', 'noarch'])

    url = f'{channel}/channeldata.json'
    logger.info(f'downloading channeldata url={url}')
    data = requests.get(url).json()
    if not (architectures <= set(data['subdirs'])):
        raise ValueError('required architectures from channel not available')

    repodata = {}
    for architecture in architectures:
        url = f'{channel}/{architecture}/repodata.json'
        logger.info(f'downloading repodata url={url}')
        repodata[architecture] = requests.get(url).json()

    return repodata
