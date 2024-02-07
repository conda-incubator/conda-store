import os
import pathlib
import sys
import tempfile
import warnings

import yaml
from conda_store_server import action, schema
from conda_store_server.action.utils import logged_command


def get_installer_platform():
    # This is how the default platform name is generated internally by
    # constructor. For example: osx-arm64, linux-64, win-64.
    # https://github.com/conda/constructor/blob/main/CONSTRUCT.md#available-platforms
    # Note: constructor is cross-friendly, see:
    # https://github.com/conda-incubator/conda-store/pull/714#discussion_r1465115323
    from conda.base.context import context

    return context.subdir


@action.action
def action_generate_constructor_installer(
    context,
    conda_command: str,
    specification: schema.CondaSpecification,
    installer_dir: pathlib.Path,
    version: str,
):
    def write_file(filename, s):
        with open(filename, "w") as f:
            context.log.info(f"{filename}:\n{s}")
            f.write(s)

    # Checks if constructor is available
    try:
        command = [
            "constructor",
            "--help",
        ]
        logged_command(context, command, timeout=10)
    except FileNotFoundError:
        warnings.warn(
            "Installer generation requires constructor: https://github.com/conda/constructor"
        )
        return

    # pip dependencies are not directly supported by constructor, they will be
    # installed via the post_install script:
    # https://github.com/conda/constructor/issues/515
    # conda and pip need to be in dependencies for the post_install script
    dependencies = ["conda", "pip"]
    pip_dependencies = []
    for d in specification.dependencies:
        if type(d) is schema.CondaSpecificationPip:
            pip_dependencies.extend(d.pip)
        else:
            dependencies.append(d)

    # Creates the construct.yaml file and post_install script
    ext = ".exe" if sys.platform == "win32" else ".sh"
    pi_ext = ".bat" if sys.platform == "win32" else ".sh"
    installer_filename = (installer_dir / specification.name).with_suffix(ext)

    os.makedirs(installer_dir, exist_ok=True)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_dir = pathlib.Path(tmp_dir)
        cache_dir = tmp_dir / "pkgs"
        tmp_dir /= "build"
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(tmp_dir, exist_ok=True)
        construct_file = tmp_dir / "construct.yaml"
        post_install_file = (tmp_dir / "post_install").with_suffix(pi_ext)

        construct = {
            "installer_filename": str(installer_filename),
            "post_install": str(post_install_file),
            "name": specification.name,
            "channels": specification.channels,
            "specs": dependencies,
            "version": version,
        }

        if sys.platform == "win32":
            post_install = """\
call "%PREFIX%\Scripts\\activate.bat"
"""
        else:
            post_install = """\
#!/usr/bin/env bash
set -euxo pipefail
source "$PREFIX/etc/profile.d/conda.sh"
conda activate "$PREFIX"
"""
        if pip_dependencies:
            post_install += f"""
python -m pip install {' '.join(pip_dependencies)}
"""

        # Writes files to disk
        write_file(construct_file, yaml.dump(construct))
        write_file(post_install_file, post_install)

        # Calls constructor
        # Note: `cache_dir` is the same as the conda `pkgs` directory. It needs
        # to be specified here because the default `pkgs` directory is not
        # available in Docker, which was causing conda's `create_cache_dir` to
        # fail.
        command = [
            "constructor",
            "-v",
            "--cache-dir",
            str(cache_dir),
            "--platform",
            get_installer_platform(),
            str(tmp_dir),
        ]
        logged_command(context, command)

    return installer_filename
