import json
import os
import pathlib
import subprocess
import typing

import yaml
from conda_lock.conda_lock import run_lock
from conda_store_server import action, conda_utils, schema


@action.action
def action_solve_lockfile(
    context,
    conda_command: str,
    specification: schema.CondaSpecification,
    platforms: typing.List[str] = [conda_utils.conda_platform()],
    # Avoids package compatibility issues, see:
    # https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html
    conda_flags: str = "--strict-channel-priority",
):
    environment_filename = pathlib.Path.cwd() / "environment.yaml"
    lockfile_filename = pathlib.Path.cwd() / "conda-lock.yaml"

    with environment_filename.open("w") as f:
        json.dump(specification.dict(), f)

    def print_cmd(cmd):
        context.log.info(f"Running command: {' '.join(cmd)}")
        context.log.info(
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, encoding="utf-8")
        )

    # The info command can be used with either mamba or conda
    print_cmd([conda_command, "info"])
    # The config command is not supported by mamba
    print_cmd(["conda", "config", "--show"])
    print_cmd(["conda", "config", "--show-sources"])

    # CONDA_FLAGS is used by conda-lock in conda_solver.solve_specs_for_arch
    try:
        conda_flags_name = "CONDA_FLAGS"
        print(f"{conda_flags_name}={conda_flags}")
        os.environ[conda_flags_name] = conda_flags

        run_lock(
            environment_files=[environment_filename],
            platforms=platforms,
            lockfile_path=lockfile_filename,
            conda_exe=conda_command,
        )
    finally:
        os.environ.pop(conda_flags_name, None)

    with lockfile_filename.open() as f:
        return yaml.safe_load(f)
