import tempfile
import pathlib
import typing
import json

import yaml

from conda_store_server import schema, utils, conda

from conda_lock.conda_lock import run_lock


def action_solve_lockfile(
    io: typing.TextIO,
    conda_command: str,
    specification: schema.Specification,
    platforms: typing.List[str] = [conda.conda_platform()],
) -> typing.Dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        environment_filename = pathlib.Path(tmpdir) / "environment.yaml"
        lockfile_filename = pathlib.Path(tmpdir) / "conda-lock.yaml"

        with environment_filename.open("w") as f:
            json.dump(specification.spec, f)

        with utils.chdir(tmpdir):
            run_lock(
                environment_files=[environment_filename],
                platforms=platforms,
                lockfile_path=lockfile_filename,
                conda_exe=conda_command,
            )

        with lockfile_filename.open() as f:
            return yaml.safe_load(f)
