import typing
import tempfile
import pathlib

import conda_pack

from conda_store_server import utils


def action_generate_conda_pack(
    io: typing.TextIO,
    conda_prefix: pathlib.Path,
    output_filename: pathlib.Path,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        with utils.chdir(tmpdir):
            conda_pack.pack(
                prefix=str(conda_prefix),
                output=str(output_filename),
                ignore_missing_files=True,
            )
