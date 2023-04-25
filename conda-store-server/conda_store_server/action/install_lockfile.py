import typing
import pathlib
import subprocess
import tempfile
import json

from conda_store_server import utils


def action_install_lockfile(
    io: typing.TextIO,
    conda_lock_spec: typing.Dict,
    conda_prefix: pathlib.Path,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        with utils.chdir(tmpdir):
            lockfile_filename = pathlib.Path(tmpdir) / "conda-lock.yml"
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

            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
            )
            io.write(output)
