import io
import os
import shlex
import subprocess
import tarfile
from typing import List

from conda_store import api
from conda_store.exception import CondaStoreError


async def run_build(
    conda_store_api: api.CondaStoreAPI,
    directory: str,
    build_id: int,
    command: List[str],
    artifact="archive",
):
    if artifact == "archive":
        await run_build_archive(conda_store_api, directory, build_id, command)
    else:
        raise CondaStoreError(f"Running build artifact {artifact} not supported")


async def run_build_archive(
    conda_store_api: api.CondaStoreAPI,
    conda_prefix: str,
    build_id: int,
    command: List[str],
):
    activate = os.path.join(conda_prefix, "bin", "activate")
    conda_unpack = os.path.join(conda_prefix, "bin", "conda-unpack")

    if not os.path.isfile(activate):
        content = await conda_store_api.download(build_id, "archive")
        content = io.BytesIO(content)

        tarfile.open(fileobj=content, mode="r:gz").extractall(path=conda_prefix)

        if os.path.exists(conda_unpack):
            subprocess.check_output(conda_unpack)

    wrapped_command = [
        "bash",
        "-c",
        ". '{}' '{}' && exec {}".format(
            activate, conda_prefix, " ".join(shlex.quote(c) for c in command)
        ),
    ]
    os.execvp(wrapped_command[0], wrapped_command)
