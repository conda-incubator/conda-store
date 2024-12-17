# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import mock

import pytest
import yaml
from conda_lock._vendor.poetry.utils._compat import CalledProcessError

from conda_store_server._internal import conda_utils
from conda_store_server._internal.plugins.lock.conda_lock import conda_lock
from conda_store_server.plugins import plugin_context


@pytest.mark.parametrize(
    "specification",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
@mock.patch("conda_store_server._internal.plugins.lock.conda_lock.conda_lock.run_lock")
@pytest.mark.long_running_test
def test_solve_lockfile(
    mock_run_lock,
    conda_store,
    specification,
    request,
):
    """Test that the call to conda_lock.run_lock is formed correctly."""

    # Dump dummy data to the expected lockfile output location
    def run_lock_side_effect(lockfile_path, **kwargs):
        with open(lockfile_path, "w") as f:
            yaml.dump({"foo": "bar"}, f)

    mock_run_lock.side_effect = run_lock_side_effect

    platforms = [conda_utils.conda_platform()]
    specification = request.getfixturevalue(specification)
    if specification.variables is None:
        cuda_version = None
    else:
        cuda_version = specification.variables.get("CONDA_OVERRIDE_CUDA")

    locker = conda_lock.CondaLock()
    lock_result = locker.lock_environment(
        context=plugin_context.PluginContext(conda_store),
        spec=specification,
        platforms=platforms,
    )

    # Check that the call to `conda_lock` is correctly formed
    mock_run_lock.assert_called_once()
    call_args = mock_run_lock.call_args_list[0][1]
    assert str(call_args["environment_files"][0]).endswith("environment.yaml")
    assert call_args["platforms"] == platforms
    assert str(call_args["lockfile_path"]).endswith("conda-lock.yaml")
    assert call_args["conda_exe"] == "mamba"
    assert call_args["with_cuda"] == cuda_version

    assert lock_result["foo"] == "bar"


def test_solve_lockfile_simple(conda_store, simple_specification):
    locker = conda_lock.CondaLock()
    lock_result = locker.lock_environment(
        context=plugin_context.PluginContext(conda_store),
        spec=simple_specification,
        platforms=[conda_utils.conda_platform()],
    )
    assert len(lock_result["package"]) != 0
    assert "zlib" in [pkg["name"] for pkg in lock_result["package"]]


@pytest.mark.parametrize(
    "specification",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
@pytest.mark.long_running_test
def test_solve_lockfile_multiple_platforms(conda_store, specification, request):
    specification = request.getfixturevalue(specification)
    locker = conda_lock.CondaLock()
    lock_result = locker.lock_environment(
        context=plugin_context.PluginContext(conda_store),
        spec=specification,
        platforms=["win-64", "osx-arm64"],
    )
    assert len(lock_result["package"]) != 0


def test_solve_lockfile_invalid_conda_flags(conda_store, simple_specification):
    """Checks that conda_flags is used by conda-lock"""
    locker = conda_lock.CondaLock()

    # Set invalid conda flags
    conda_store.config.conda_flags = "--this-is-invalid"

    with pytest.raises(
        CalledProcessError,
        match=(r"Command.*--this-is-invalid.*returned non-zero exit status"),
    ):
        locker.lock_environment(
            context=plugin_context.PluginContext(conda_store),
            spec=simple_specification,
            platforms=[conda_utils.conda_platform()],
        )
