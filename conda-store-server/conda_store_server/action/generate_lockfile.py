import json
import os
import pathlib
import typing

import yaml
from conda_lock.conda_lock import run_lock
from conda_store_server import action, conda_utils, schema
from conda_store_server.action.utils import logged_command


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

    # The info command can be used with either mamba or conda
    logged_command(context, [conda_command, "info"])
    # The config command is not supported by mamba
    logged_command(context, ["conda", "config", "--show"])
    logged_command(context, ["conda", "config", "--show-sources"])

    # conda-lock ignores variables defined in the specification, so this code
    # gets the value of CONDA_OVERRIDE_CUDA and passes it to conda-lock via
    # the with_cuda parameter, see:
    # https://github.com/conda-incubator/conda-store/issues/719
    # https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-virtual.html#overriding-detected-packages
    # TODO: Support all variables once upstream fixes are made to conda-lock,
    # see the discussion in issue 719.
    if specification.variables is not None:
        cuda_version = specification.variables.get("CONDA_OVERRIDE_CUDA")
    else:
        cuda_version = None

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
            with_cuda=cuda_version,
        )
    finally:
        os.environ.pop(conda_flags_name, None)

    with lockfile_filename.open() as f:
        return yaml.safe_load(f)
