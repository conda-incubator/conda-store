import typing
import tempfile
import pathlib
import json
import subprocess

from conda_store_server import utils


def action_generate_conda_export(
    io: typing.TextIO, conda_command: str, conda_prefix: pathlib.Path
):
    with tempfile.TemporaryDirectory() as tmpdir:
        with utils.chdir(tmpdir):
            command = [
                conda_command,
                "env",
                "export",
                "--prefix",
                str(conda_prefix),
                "--json",
            ]

            output = subprocess.check_output(
                command,
                encoding="utf-8",
            )
            return json.loads(output)
