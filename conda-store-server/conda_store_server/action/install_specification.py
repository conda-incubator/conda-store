import typing
import tempfile
import pathlib
import json
import subprocess

from conda_store_server import conda, utils, schema


def action_install_specification(
    io: typing.TextIO,
    conda_command: str,
    specification: schema.Specification,
    conda_prefix: pathlib.Path,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        environment_filename = pathlib.Path(tmpdir) / "environment.yaml"
        with environment_filename.open("w") as f:
            json.dump(specification.spec, f)

        command = [
            conda_command,
            "env",
            "create",
            "-p",
            str(conda_prefix),
            "-f",
            str(environment_filename),
        ]

        with utils.chdir(tmpdir):
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
            )
            io.write(output)
