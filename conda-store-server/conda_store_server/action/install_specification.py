import json
import pathlib

from conda_store_server import action, schema


@action.action
def action_install_specification(
    context,
    conda_command: str,
    specification: schema.CondaSpecification,
    conda_prefix: pathlib.Path,
):
    environment_filename = pathlib.Path.cwd() / "environment.yaml"
    with environment_filename.open("w") as f:
        json.dump(specification.dict(), f)

    command = [
        conda_command,
        "env",
        "create",
        "-p",
        str(conda_prefix),
        "-f",
        str(environment_filename),
    ]

    context.run(command, check=True)
