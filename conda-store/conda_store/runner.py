import os
import io
import tarfile
import subprocess
import shlex

from conda_store.exception import CondaStoreError


async def run_build(
    conda_store_api: "CondaStoreAPI",
    directory: str,
    build_id: int,
    command: str,
    artifact="archive",
):
    if artifact == "archive":
        await run_build_archive(conda_store_api, directory, build_id, command)
    else:
        raise CondaStoreError(f"Running build artifact {artifact} not supported")


async def run_build_archive(
    conda_store_api: "CondaStoreAPI",
    conda_prefix: str,
    build_id: int,
    command: str,
):
    activate = os.path.join(conda_prefix, 'bin', 'activate')
    conda_unpack = os.path.join(conda_prefix, 'bin', 'conda-unpack')
    quoted_command = [shlex.quote(c) for c in shlex.split(command)]

    if not os.path.isfile(activate):
        content = await conda_store_api.download(build_id, "archive")
        content = io.BytesIO(content)

        tarfile.open(fileobj=content, mode='r:gz').extractall(path=conda_prefix)

        if os.path.exists(conda_unpack):
            subprocess.check_output(conda_unpack)

    wrapped_command = [
        "bash",
        "-c",
        ". '{}' '{}' && echo CONDA_PREFIX=$CONDA_PREFIX && echo $PATH && {}".format(activate, conda_prefix, ' '.join(quoted_command))
    ]
    os.execvp(wrapped_command[0], wrapped_command)
