import asyncio
import pathlib
import re
import sys

import pytest
from conda_store_server import action, api, conda_utils, orm, schema, server, utils
from conda_store_server.server.auth import DummyAuthentication
from fastapi import Request
from fastapi.responses import RedirectResponse


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
        platforms=[conda_utils.conda_platform()],
    )
    assert len(context.result["package"]) != 0


@pytest.mark.parametrize(
    "specification",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
def test_solve_lockfile_multiple_platforms(conda_store, specification, request):
    specification = request.getfixturevalue(specification)
    context = action.action_solve_lockfile(
        conda_command=conda_store.conda_command,
        specification=specification,
        platforms=["osx-64", "linux-64", "win-64", "osx-arm64"],
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

    assert conda_utils.is_conda_prefix(conda_prefix)


def test_install_lockfile(tmp_path, conda_store, simple_conda_lock):
    conda_prefix = tmp_path / "test"

    action.action_install_lockfile(
        conda_lock_spec=simple_conda_lock, conda_prefix=conda_prefix
    )

    assert conda_utils.is_conda_prefix(conda_prefix)


def test_generate_conda_export(conda_store, conda_prefix):
    context = action.action_generate_conda_export(
        conda_command=conda_store.conda_command, conda_prefix=conda_prefix
    )
    # The env name won't be correct because conda only sets the env name when
    # an environment is in an envs dir. See the discussion on PR #549.
    context.result['name'] = 'test-prefix'

    schema.CondaSpecification.parse_obj(context.result)


def test_generate_conda_pack(tmp_path, conda_prefix):
    output_filename = tmp_path / "environment.tar.gz"

    action.action_generate_conda_pack(
        conda_prefix=conda_prefix,
        output_filename=output_filename,
    )

    assert output_filename.exists()


@pytest.mark.skipif(sys.platform != "linux", reason="conda-docker only works on linux")
def test_generate_conda_docker(conda_store, conda_prefix):
    action.action_generate_conda_docker(
        conda_prefix=conda_prefix,
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

    assert conda_utils.is_conda_prefix(conda_prefix)

    action.action_remove_conda_prefix(conda_prefix)

    assert not conda_utils.is_conda_prefix(conda_prefix)
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


def test_add_conda_prefix_packages(db, conda_store, simple_specification, conda_prefix):
    build_id = conda_store.register_environment(
        db, specification=simple_specification, namespace="pytest"
    )

    action.action_add_conda_prefix_packages(
        db=db,
        conda_prefix=conda_prefix,
        build_id=build_id,
    )

    build = api.get_build(db, build_id=build_id)
    assert len(build.package_builds) > 0


def test_add_lockfile_packages(
    db, conda_store, simple_specification, simple_conda_lock
):
    task, solve_id = conda_store.register_solve(db, specification=simple_specification)

    action.action_add_lockfile_packages(
        db=db,
        conda_lock_spec=simple_conda_lock,
        solve_id=solve_id,
    )

    solve = api.get_solve(db, solve_id=solve_id)
    assert len(solve.package_builds) > 0


@pytest.mark.parametrize(
    "is_legacy_build",
    [
        False,
        True,
    ],
)
def test_api_get_build_lockfile(
    request, conda_store, db, simple_specification_with_pip, conda_prefix, is_legacy_build
):
    # initializes data needed to get the lockfile
    specification = simple_specification_with_pip
    namespace = "pytest"

    class MyAuthentication(DummyAuthentication):
        # Skips auth (used in api_get_build_lockfile). Test version of request
        # has no state attr, which is returned in the real impl of this method.
        # So I have to overwrite the method itself.
        def authorize_request(self, *args, **kwargs):
            pass

    auth = MyAuthentication()
    build_id = conda_store.register_environment(
        db, specification=specification, namespace=namespace
    )
    db.commit()
    build = api.get_build(db, build_id=build_id)
    environment = api.get_environment(db, namespace=namespace)

    # adds packages (returned in the lockfile)
    action.action_add_conda_prefix_packages(
        db=db,
        conda_prefix=conda_prefix,
        build_id=build_id,
    )

    key = "" if is_legacy_build else build.conda_lock_key

    # creates build artifacts
    build_artifact = orm.BuildArtifact(
        build_id=build_id,
        build=build,
        artifact_type=schema.BuildArtifactType.LOCKFILE,
        key=key,  # key value determines returned lockfile type
    )
    db.add(build_artifact)
    db.commit()

    # gets lockfile for this build
    res = asyncio.run(
        server.views.api.api_get_build_lockfile(
            request=request,
            conda_store=conda_store,
            auth=auth,
            namespace=namespace,
            environment_name=environment.name,
            build_id=build_id,
    ))

    if key == "":
        # legacy build: returns pinned package list
        lines = res.split("\n")
        assert len(lines) > 2
        assert lines[:2] == [
            f"#platform: {conda_utils.conda_platform()}",
            "@EXPLICIT",
        ]
        assert re.match("http.*//.*tar.bz2#.*", lines[2]) is not None
    else:
        # new build: redirects to lockfile generated by conda-lock
        lockfile_url_pattern = (
            "lockfile/"
            "89e5a99aa094689b7aafc66c47987fa186e08f9d619a02ab1a469d0759da3b8b-"
            ".*-test.yml"
        )
        assert type(res) is RedirectResponse
        assert key == res.headers['location']
        assert re.match(lockfile_url_pattern, res.headers['location']) is not None
        assert res.status_code == 307
