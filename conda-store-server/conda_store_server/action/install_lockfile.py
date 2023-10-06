import json
import pathlib
import typing

from conda_store_server import action


@action.action
def action_install_lockfile(
    context,
    conda_lock_spec: typing.Dict,
    conda_prefix: pathlib.Path,
):
    lockfile_filename = pathlib.Path.cwd() / "conda-lock.yml"
    with lockfile_filename.open("w") as f:
        json.dump(conda_lock_spec, f)

    command = [
        "conda-lock",
        "install",
        "--validate-platform",
        "--log-level",
        "INFO",
        "--prefix",
        str(conda_prefix),
        str(lockfile_filename),
    ]

    context.run(command, check=True)
