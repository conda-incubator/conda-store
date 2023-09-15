import json
import pathlib
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
):
    environment_filename = pathlib.Path.cwd() / "environment.yaml"
    lockfile_filename = pathlib.Path.cwd() / "conda-lock.yaml"

    with environment_filename.open("w") as f:
        json.dump(specification.dict(), f)

    run_lock(
        environment_files=[environment_filename],
        platforms=platforms,
        lockfile_path=lockfile_filename,
        conda_exe=conda_command,
    )

    with lockfile_filename.open() as f:
        return yaml.safe_load(f)
