import pytest

import io

from conda_store_server import action, conda


@pytest.mark.parametrize(
    "specification",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
def test_lockfile_action(conda_store, specification, request):
    output = io.StringIO()
    specification = request.getfixturevalue(specification)
    lock_specification = action.action_solve_lockfile(
        output,
        conda_command=conda_store.conda_command,
        specification=specification,
        platforms=[conda.conda_platform()],
    )
    assert len(lock_specification["package"]) != 0


def test_fetch_and_extract_conda_packages(tmp_path, simple_conda_lock):
    output = io.StringIO()

    action.action_fetch_and_extract_conda_packages(
        output,
        conda_lock_spec=simple_conda_lock,
        pkgs_dir=tmp_path,
    )

    assert output.getvalue()


def test_install_specification(tmp_path, conda_store, simple_specification):
    output = io.StringIO()

    action.action_install_specification(
        output,
        conda_command=conda_store.conda_command,
        specification=simple_specification,
        conda_prefix=tmp_path,
    )
