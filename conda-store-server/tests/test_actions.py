import pytest

import pathlib
import sys

from conda_store_server import action, conda, utils, schema, api


def test_action_decorator():
    @action.action
    def test_function(context):
        print("stdout")
        print("stderr", file=sys.stderr)
        context.run(["echo", "subprocess"])
        context.run("echo subprocess_stdout", shell=True)
        context.run("echo subprocess_stderr 1>&2", shell=True)
        context.log.info("log")
        return pathlib.Path.cwd()

    context = test_function()
    assert (
        context.stdout.getvalue()
        == "stdout\nstderr\nsubprocess\nsubprocess_stdout\nsubprocess_stderr\nlog\n"
    )
    # test that action direction is not the same as outside function
    assert context.result != pathlib.Path.cwd()
    # test that temportary directory is cleaned up
    assert not context.result.exists()


@pytest.mark.parametrize(
    "specification",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
def test_solve_lockfile(conda_store, specification, request):
    specification = request.getfixturevalue(specification)
    context = action.action_solve_lockfile(
        conda_command=conda_store.conda_command,
        specification=specification,
        platforms=[conda.conda_platform()],
    )
    assert len(context.result["package"]) != 0


def test_fetch_and_extract_conda_packages(tmp_path, simple_conda_lock):
    context = action.action_fetch_and_extract_conda_packages(
        conda_lock_spec=simple_conda_lock,
        pkgs_dir=tmp_path,
    )

    assert context.stdout.getvalue()


def test_install_specification(tmp_path, conda_store, simple_specification):
    conda_prefix = tmp_path / "test"

    action.action_install_specification(
        conda_command=conda_store.conda_command,
        specification=simple_specification,
        conda_prefix=conda_prefix,
    )

    assert conda.is_conda_prefix(conda_prefix)


def test_install_lockfile(tmp_path, conda_store, simple_conda_lock):
    conda_prefix = tmp_path / "test"

    action.action_install_lockfile(
        conda_lock_spec=simple_conda_lock, conda_prefix=conda_prefix
    )

    assert conda.is_conda_prefix(conda_prefix)


def test_generate_conda_export(conda_store, current_prefix):
    context = action.action_generate_conda_export(
        conda_command=conda_store.conda_command, conda_prefix=current_prefix
    )

    schema.CondaSpecification.parse_obj(context.result)


def test_generate_conda_pack(tmp_path, current_prefix):
    output_filename = tmp_path / "environment.tar.gz"

    action.action_generate_conda_pack(
        conda_prefix=current_prefix,
        output_filename=output_filename,
    )

    assert output_filename.exists()


@pytest.mark.xfail
def test_generate_conda_docker(conda_store, current_prefix):
    action.action_generate_conda_docker(
        conda_prefix=current_prefix,
        default_docker_image=utils.callable_or_value(
            conda_store.default_docker_base_image, None
        ),
        container_registry=conda_store.container_registry,
        output_image_name="test",
        output_image_tag="tag",
    )


def test_remove_not_conda_prefix(tmp_path):
    fake_conda_prefix = tmp_path / "test"
    fake_conda_prefix.mkdir()

    with pytest.raises(ValueError):
        action.action_remove_conda_prefix(fake_conda_prefix)


def test_remove_conda_prefix(tmp_path, simple_conda_lock):
    conda_prefix = tmp_path / "test"

    action.action_install_lockfile(
        conda_lock_spec=simple_conda_lock, conda_prefix=conda_prefix
    )

    assert conda.is_conda_prefix(conda_prefix)

    action.action_remove_conda_prefix(conda_prefix)

    assert not conda.is_conda_prefix(conda_prefix)
    assert not conda_prefix.exists()


def test_set_conda_prefix_permissions(tmp_path, conda_store, simple_conda_lock):
    conda_prefix = tmp_path / "test"

    action.action_install_lockfile(
        conda_lock_spec=simple_conda_lock, conda_prefix=conda_prefix
    )

    context = action.action_set_conda_prefix_permissions(
        conda_prefix=conda_prefix,
        permissions="755",
        uid=None,
        gid=None,
    )
    assert "no changes for permissions of conda_prefix" in context.stdout.getvalue()
    assert "no changes for gid and uid of conda_prefix" in context.stdout.getvalue()


def test_get_conda_prefix_stats(tmp_path, conda_store, simple_conda_lock):
    conda_prefix = tmp_path / "test"

    action.action_install_lockfile(
        conda_lock_spec=simple_conda_lock, conda_prefix=conda_prefix
    )

    context = action.action_get_conda_prefix_stats(conda_prefix)
    assert context.result["disk_usage"] > 0


def test_add_conda_prefix_packages(conda_store, simple_specification, current_prefix):
    build_id = conda_store.register_environment(
        specification=simple_specification.spec, namespace="pytest"
    )

    action.action_add_conda_prefix_packages(
        db=conda_store.db,
        conda_prefix=current_prefix,
        build_id=build_id,
    )

    build = api.get_build(conda_store.db, build_id=build_id)
    assert len(build.package_builds) > 0


def test_add_lockfile_packages(
    conda_store, simple_specification, simple_conda_lock, current_prefix
):
    conda_specification = schema.CondaSpecification.parse_obj(simple_specification.spec)

    task, solve_id = conda_store.register_solve(specification=conda_specification)

    action.action_add_lockfile_packages(
        db=conda_store.db,
        conda_lock_spec=simple_conda_lock,
        solve_id=solve_id,
    )

    solve = api.get_solve(conda_store.db, solve_id=solve_id)
    assert len(solve.package_builds) > 0
