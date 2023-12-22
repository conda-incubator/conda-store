import os
import pathlib
import subprocess
import sys
import tempfile

import yaml
from conda_store_server import action, schema


@action.action
def action_generate_constructor_installer(
    context,
    conda_command: str,
    specification: schema.CondaSpecification,
    installer_dir: pathlib.Path,
    version: str,
):
    # Helpers
    def print_cmd(cmd):
        context.log.info(f"Running command: {' '.join(cmd)}")
        context.log.info(
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, encoding="utf-8")
        )

    def write_file(filename, s):
        with open(filename, "w") as f:
            context.log.info(f"{filename}:\n{s}")
            f.write(s)

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
        construct_file = tmp_dir / "construct.yaml"
        post_install_file = (tmp_dir / "post_install").with_suffix(pi_ext)
        env_dir = tmp_dir / "env"

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
call "%PREFIX%\Scripts\activate.bat"
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
pip install {' '.join(pip_dependencies)}
"""

        # Writes files to disk
        write_file(construct_file, yaml.dump(construct))
        write_file(post_install_file, post_install)

        # Installs constructor
        command = [
            conda_command,
            "create",
            "-y",
            "-p",
            str(env_dir),
            "constructor",
        ]
        print_cmd(command)

        # Calls constructor
        command = [
            conda_command,
            "run",
            "-p",
            str(env_dir),
            "--no-capture-output",
            "constructor",
            str(tmp_dir),
        ]
        print_cmd(command)

    return installer_filename
