import pathlib
import stat

from conda_store_server import action, conda_utils, utils


@action.action
def action_set_conda_prefix_permissions(
    context,
    conda_prefix: pathlib.Path,
    permissions: str,
    uid: int,
    gid: int,
):
    conda_prefix = conda_prefix.resolve()

    # safeguard to try and prevent destructive actions
    if not conda_utils.is_conda_prefix(conda_prefix):
        raise ValueError("not a valid conda prefix")

    stat_info = conda_prefix.stat()

    if permissions is not None and oct(stat.S_IMODE(stat_info.st_mode))[-3:] != str(
        permissions
    ):
        context.log.info(
            f"modifying permissions of {conda_prefix} to permissions={permissions}"
        )
        with utils.timer(context.log, f"chmod of {conda_prefix}"):
            utils.chmod(conda_prefix, permissions)
    else:
        context.log.info(f"no changes for permissions of conda_prefix {conda_prefix}")

    if (
        uid is not None
        and gid is not None
        and (str(uid) != str(stat_info.st_uid) or str(gid) != str(stat_info.st_gid))
    ):
        context.log.info(
            f"modifying permissions of conda_prefix {conda_prefix} to uid={uid} and gid={gid}"
        )
        with utils.timer(context.log, f"chown of {conda_prefix}"):
            utils.chown(conda_prefix, uid, gid)
    else:
        context.log.info(f"no changes for gid and uid of conda_prefix {conda_prefix}")
