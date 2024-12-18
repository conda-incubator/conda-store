# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os
import pathlib
import typing

import yaml
from conda_lock.conda_lock import run_lock

from conda_store_server._internal import conda_utils, schema, utils
from conda_store_server.plugins.hookspec import hookimpl
from conda_store_server.plugins.plugin_context import PluginContext
from conda_store_server.plugins.types import lock, types


class CondaLock(lock.LockPlugin):
    def _conda_command(self, conda_store) -> str:
        settings = conda_store.get_settings()
        return settings.conda_command

    def _conda_flags(self, conda_store) -> str:
        return conda_store.config.conda_flags

    @utils.run_in_tempdir
    def lock_environment(
        self,
        context: PluginContext,
        spec: schema.CondaSpecification,
        platforms: typing.List[str] = [conda_utils.conda_platform()],
    ) -> str:
        context.log.info("lock_environment entrypoint for conda-lock")
        conda_command = self._conda_command(context.conda_store)
        conda_flags = self._conda_flags(context.conda_store)

        environment_filename = pathlib.Path.cwd() / "environment.yaml"
        lockfile_filename = pathlib.Path.cwd() / "conda-lock.yaml"

        with environment_filename.open("w") as f:
            json.dump(spec.model_dump(), f)

        context.log.info(
            "Note that the output of `conda config --show` displayed below only reflects "
            "settings in the conda configuration file, which might be overridden by "
            "variables required to be set by conda-store via the environment. Overridden "
            f"settings: CONDA_FLAGS={conda_flags}"
        )

        # The info command can be used with either mamba or conda
        context.run_command([conda_command, "info"])
        # The config command is not supported by mamba
        context.run_command(["conda", "config", "--show"])
        context.run_command(["conda", "config", "--show-sources"])

        # conda-lock ignores variables defined in the specification, so this code
        # gets the value of CONDA_OVERRIDE_CUDA and passes it to conda-lock via
        # the with_cuda parameter, see:
        # https://github.com/conda-incubator/conda-store/issues/719
        # https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-virtual.html#overriding-detected-packages
        # TODO: Support all variables once upstream fixes are made to conda-lock,
        # see the discussion in issue 719.
        if spec.variables is not None:
            cuda_version = spec.variables.get("CONDA_OVERRIDE_CUDA")
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


@hookimpl
def lock_plugins():
    """conda-lock locking plugin"""
    yield types.TypeLockPlugin(
        name="conda-lock",
        synopsis="Generate a lockfile using conda-lock",
        backend=CondaLock,
    )
