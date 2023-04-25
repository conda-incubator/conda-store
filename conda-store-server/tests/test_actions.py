import pytest

import io

from conda_store_server import action, conda, utils


@pytest.mark.parametrize(
    "specification",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
def test_solve_lockfile(conda_store, specification, request):
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


def test_install_lockfile(tmp_path, conda_store, simple_conda_lock):
    output = io.StringIO()

    action.action_install_lockfile(
        output, conda_lock_spec=simple_conda_lock, conda_prefix=tmp_path
    )


def test_generate_conda_export(conda_store, current_prefix):
    output = io.StringIO()

    conda_export = action.action_generate_conda_export(
        output, conda_command=conda_store.conda_command, conda_prefix=current_prefix
    )


def test_generate_conda_pack(tmp_path, current_prefix):
    output = io.StringIO()

    conda_export = action.action_generate_conda_pack(
        output,
        conda_prefix=current_prefix,
        output_filename=(tmp_path / "environment.tar.gz"),
    )


def test_generate_conda_docker(conda_store, current_prefix):
    output = io.StringIO()

    image = action.action_generate_conda_docker(
        output,
        conda_prefix=current_prefix,
        default_docker_image=utils.callable_or_value(
            conda_store.default_docker_base_image, None
        ),
        container_registry=conda_store.container_registry,
        output_image_name="test",
        output_image_tag="tag",
    )
    breakpoint()
