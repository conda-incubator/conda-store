# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest
import yaml
import os

from unittest import mock

from conda_store_server._internal import conda_utils
from conda_store_server.plugins import plugin_context
from conda_store_server.plugins.lock import conda_lock


@pytest.mark.parametrize(
    "specification",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
@mock.patch("conda_store_server.plugins.lock.conda_lock.run_lock")
@pytest.mark.long_running_test
def test_solve_lockfile(
    mock_run_lock,
    specification,
    tmp_path,
    request,
):
    """Test that the call to conda_lock.run_lock is formed correctly.
    """
    tmp_path.mkdir(exist_ok=True)
    os.chdir(tmp_path)

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

    locker = conda_lock.CondaLock(conda_command="mamba")
    lock_result = locker.lock_environment(
        context=plugin_context.PluginContext(),
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


def test_solve_lockfile_simple(tmp_path, simple_specification):
    tmp_path.mkdir(exist_ok=True)
    os.chdir(tmp_path)
    
    locker = conda_lock.CondaLock(
        conda_command="mamba", conda_flags="--strict-channel-priority"
    )
    lock_result = locker.lock_environment(
        context=plugin_context.PluginContext(),
        spec=simple_specification,
        platforms=[conda_utils.conda_platform()],
    )
    assert len(lock_result["package"]) != 0


@pytest.mark.parametrize(
    "specification",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
@pytest.mark.long_running_test
def test_solve_lockfile_multiple_platforms(tmp_path, specification, request):
    tmp_path.mkdir(exist_ok=True)
    os.chdir(tmp_path)

    specification = request.getfixturevalue(specification)
    locker = conda_lock.CondaLock(
        conda_command="mamba", conda_flags="--strict-channel-priority"
    )
    lock_result = locker.lock_environment(
        context=plugin_context.PluginContext(),
        spec=specification,
        platforms=["osx-64", "linux-64", "win-64", "osx-arm64"],
    )
    assert len(lock_result["package"]) != 0

# Checks that conda_flags is used by conda-lock
def test_solve_lockfile_invalid_conda_flags(tmp_path, simple_specification):
    tmp_path.mkdir(exist_ok=True)
    os.chdir(tmp_path)

    locker = conda_lock.CondaLock(
        conda_command="mamba", conda_flags="--this-is-invalid"
    )

    with pytest.raises(
        Exception, match=(r"Command.*--this-is-invalid.*returned non-zero exit status")
    ):
         locker.lock_environment(
            context=plugin_context.PluginContext(),
            spec=simple_specification,
            platforms=[conda_utils.conda_platform()],
        )
