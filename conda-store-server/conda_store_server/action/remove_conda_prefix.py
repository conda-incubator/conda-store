import shutil
import pathlib

from conda_store_server import conda_utils, action


@action.action
def action_remove_conda_prefix(
    context,
    conda_prefix: pathlib.Path,
):
    # safeguard to try and prevent destructive actions
    if not conda_utils.is_conda_prefix(conda_prefix):
        raise ValueError("given prefix is not a conda environment")

    context.log.info(f'removing conda prefix "{conda_prefix.resolve()}"')
    shutil.rmtree(conda_prefix)
