import json
import os
import pathlib
import sys
import tempfile
import typing

from conda_store_server import action


@action.action
def action_install_lockfile(
    context,
    conda_lock_spec: typing.Dict,
    conda_prefix: pathlib.Path,
):
    lockfile_filename = pathlib.Path.cwd() / "conda-lock.yml"
    with lockfile_filename.open("w") as f:
        json.dump(conda_lock_spec, f)

    # This essentially disables caching by having a dedicated cache per
    # environment. This is necessary because concurrent jobs override packages
    # in the shared cache, which leads to failed builds.
    #
    # For example, packages A and B use the same dependency. Package A starts
    # the download process and puts the dependency in the cache. Package B sees
    # that the dependency is in the cache and tries to use it, but the
    # dependency can be in an invalid state, such as being not fully-copied or
    # downloaded, because the cache operations are not atomic, so the build of
    # package B fails.
    #
    # This is a known problem in conda and I'm not aware of any solution besides
    # just disabling the cache by having a per-environment temporary cache
    # directory. The name of the temporary directory is returned from this
    # action so that the directory can be deleted once the package is done
    # building, as that requires having access to dependencies from the cache.
    #
    # Here are the relevant issues from the upstream repo, but they were closed
    # without any solution:
    # https://github.com/conda/conda/issues/9447
    # https://github.com/conda/conda/issues/5997
    # https://github.com/conda/conda/issues/7741
    tmp_pkgs_dir = tempfile.TemporaryDirectory()
    env = os.environ.copy()
    env["CONDA_PKGS_DIRS"] = tmp_pkgs_dir.name

    command = [
        sys.executable,
        "-m",
        "conda_lock",
        "install",
        "--validate-platform",
        "--log-level",
        "INFO",
        "--prefix",
        str(conda_prefix),
        str(lockfile_filename),
    ]

    context.run(command, check=True, env=env)

    return tmp_pkgs_dir
