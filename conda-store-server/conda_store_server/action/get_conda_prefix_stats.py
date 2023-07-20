import pathlib

from conda_store_server import action, conda_utils, utils


@action.action
def action_get_conda_prefix_stats(context, conda_prefix: pathlib.Path):
    # safeguard to try and prevent destructive actions
    if not conda_utils.is_conda_prefix(conda_prefix):
        raise ValueError("given prefix is not a conda environment")

    stats = {}
    stats["disk_usage"] = int(utils.disk_usage(conda_prefix))
    return stats
