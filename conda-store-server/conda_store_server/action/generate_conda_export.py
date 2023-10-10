import json
import pathlib

from conda_store_server import action


@action.action
def action_generate_conda_export(
    context, conda_command: str, conda_prefix: pathlib.Path
):
    command = [
        conda_command,
        "env",
        "export",
        "--prefix",
        str(conda_prefix),
        "--json",
    ]

    result = context.run(command, check=True, redirect_stderr=False)
    if result.stderr:
        context.log.warning(f"conda env export stderr: {result.stderr}")
    return json.loads(result.stdout)
