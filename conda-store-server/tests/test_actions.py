import asyncio
import datetime
import pathlib
import re
import subprocess
import sys

import pytest
import yarl
from conda_store_server import (
    BuildKey,
    action,
    api,
    conda_utils,
    orm,
    schema,
    server,
    utils,
)
from conda_store_server.server.auth import DummyAuthentication
from fastapi.responses import RedirectResponse
from traitlets import TraitError


def test_action_decorator():
    @action.action
    def test_function(context):
        print("stdout")
        print("stderr", file=sys.stderr)
        if sys.platform == "win32":
            # echo is not a separate program on Windows
            context.run(["cmd", "/c", "echo subprocess"])
            context.run("echo subprocess_stdout", shell=True)
            context.run("echo subprocess_stderr>&2", shell=True)
            context.run(
                "echo subprocess_stderr_no_redirect>&2",
                shell=True,
                redirect_stderr=False,
            )
        else:
            context.run(["echo", "subprocess"])
            context.run("echo subprocess_stdout", shell=True)
            context.run("echo subprocess_stderr 1>&2", shell=True)
            context.run(
                "echo subprocess_stderr_no_redirect 1>&2",
                shell=True,
                redirect_stderr=False,
            )
        context.log.info("log")
        return pathlib.Path.cwd()

    context = test_function()
    assert (
        context.stdout.getvalue()
        == "stdout\nstderr\nsubprocess\nsubprocess_stdout\nsubprocess_stderr\nlog\n"
    )
    assert context.stderr.getvalue() == "subprocess_stderr_no_redirect\n"
    # test that action direction is not the same as outside function
    assert context.result != pathlib.Path.cwd()
    # test that temporary directory is cleaned up
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


def test_solve_lockfile_valid_conda_flags(conda_store, simple_specification):
    context = action.action_solve_lockfile(
        conda_command=conda_store.conda_command,
        specification=simple_specification,
        platforms=[conda_utils.conda_platform()],
        conda_flags="--strict-channel-priority",
    )
    assert len(context.result["package"]) != 0


# Checks that conda_flags is used by conda-lock
def test_solve_lockfile_invalid_conda_flags(conda_store, simple_specification):
    with pytest.raises(
        Exception, match=(r"Command.*--this-is-invalid.*returned non-zero exit status")
    ):
        action.action_solve_lockfile(
            conda_command=conda_store.conda_command,
            specification=simple_specification,
            platforms=[conda_utils.conda_platform()],
            conda_flags="--this-is-invalid",
        )


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


@pytest.mark.parametrize(
    "specification_name",
    [
        "simple_specification",
        "simple_specification_with_pip",
    ],
)
def test_generate_constructor_installer(
    conda_store, specification_name, request, tmp_path
):
    specification = request.getfixturevalue(specification_name)
    installer_dir = tmp_path / "installer_dir"

    # Creates the installer
    context = action.action_generate_constructor_installer(
        conda_command=conda_store.conda_command,
        specification=specification,
        installer_dir=installer_dir,
        version="1",
    )

    # Checks that the installer was created
    installer = context.result
    assert installer.exists()

    tmp_dir = tmp_path / "tmp"

    # Runs the installer
    out_dir = pathlib.Path(tmp_dir) / "out"
    if sys.platform == "win32":
        subprocess.check_output([installer, "/S", f"/D={out_dir}"])
    else:
        subprocess.check_output([installer, "-b", "-p", str(out_dir)])

    # Checks the output directory
    assert out_dir.exists()
    lib_dir = out_dir / "lib"
    if specification_name == "simple_specification":
        if sys.platform == "win32":
            assert any(str(x).endswith("zlib.dll") for x in out_dir.iterdir())
        elif sys.platform == "darwin":
            assert any(str(x).endswith("libz.dylib") for x in lib_dir.iterdir())
        else:
            assert any(str(x).endswith("libz.so") for x in lib_dir.iterdir())
    else:
        # Uses rglob to not depend on the version of the python
        # directory, which is where site-packages is located
        flask = pathlib.Path("site-packages") / "flask"
        assert any(str(x).endswith(str(flask)) for x in out_dir.rglob("*"))


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
    context.result["name"] = "test-prefix"

    schema.CondaSpecification.parse_obj(context.result)


def test_generate_conda_pack(tmp_path, conda_prefix):
    output_filename = tmp_path / "environment.tar.gz"

    action.action_generate_conda_pack(
        conda_prefix=conda_prefix,
        output_filename=output_filename,
    )

    assert output_filename.exists()


@pytest.mark.xfail(
    reason=(
        "Generating Docker images is currently not supported, see "
        "https://github.com/conda-incubator/conda-store/issues/666"
    )
)
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


@pytest.mark.skipif(
    sys.platform == "win32", reason="permissions are not supported on Windows"
)
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
    "is_legacy_build, build_key_version",
    [
        (False, 0),  # invalid
        (False, 1),  # long (legacy)
        (False, 2),  # short (default)
        (True, 1),  # build_key_version doesn't matter because there's no lockfile
    ],
)
def test_api_get_build_lockfile(
    request,
    conda_store,
    db,
    simple_specification_with_pip,
    conda_prefix,
    is_legacy_build,
    build_key_version,
):
    # sets build_key_version
    if build_key_version == 0:  # invalid
        with pytest.raises(
            TraitError,
            match=(
                r"c.CondaStore.build_key_version: invalid build key version: 0, "
                r"expected: \(1, 2\)"
            ),
        ):
            conda_store.build_key_version = build_key_version
        return  # invalid, nothing more to test
    conda_store.build_key_version = build_key_version
    assert BuildKey.current_version() == build_key_version
    assert BuildKey.versions() == (1, 2)

    # initializes data needed to get the lockfile
    specification = simple_specification_with_pip
    specification.name = "this-is-a-long-environment-name"
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
    # makes this more visible in the lockfile
    build_id = 12345678
    build.id = build_id
    # makes sure the timestamp in build_key is always the same
    build.scheduled_on = datetime.datetime(2023, 11, 5, 3, 54, 10, 510258)
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
        )
    )

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
        def lockfile_url(build_key):
            return f"lockfile/{build_key}.yml"

        if build_key_version == 1:
            build_key = (
                "c7afdeffbe2bda7d16ca69beecc8bebeb29280a95d4f3ed92849e4047710923b-"
                "20231105-035410-510258-12345678-this-is-a-long-environment-name"
            )
        elif build_key_version == 2:
            build_key = "c7afdeff-1699156450-12345678-this-is-a-long-environment-name"
        else:
            raise ValueError(f"unexpected build_key_version: {build_key_version}")
        assert type(res) is RedirectResponse
        assert key == res.headers["location"]
        assert build.build_key == build_key
        assert BuildKey.get_build_key(build) == build_key
        assert build.parse_build_key(build_key) == 12345678
        assert BuildKey.parse_build_key(build_key) == 12345678
        assert lockfile_url(build_key) == build.conda_lock_key
        assert lockfile_url(build_key) == res.headers["location"]
        assert res.status_code == 307


def test_api_get_build_installer(
    request, conda_store, db, simple_specification_with_pip, conda_prefix
):
    # initializes data needed to get the installer
    specification = simple_specification_with_pip
    specification.name = "my-env"
    namespace = "pytest"

    class MyAuthentication(DummyAuthentication):
        # Skips auth (used in api_get_build_installer). Test version of request
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

    # creates build artifacts
    build_artifact = orm.BuildArtifact(
        build_id=build_id,
        build=build,
        artifact_type=schema.BuildArtifactType.CONSTRUCTOR_INSTALLER,
        key=build.constructor_installer_key,
    )
    db.add(build_artifact)
    db.commit()

    # gets installer for this build
    res = asyncio.run(
        server.views.api.api_get_build_installer(
            request=request,
            conda_store=conda_store,
            auth=auth,
            build_id=build_id,
        )
    )

    # redirects to installer
    def installer_url(build_key):
        ext = "exe" if sys.platform == "win32" else "sh"
        return f"installer/{build_key}.{ext}"

    assert type(res) is RedirectResponse
    assert build.constructor_installer_key == res.headers["location"]
    assert installer_url(build.build_key) == build.constructor_installer_key
    assert res.status_code == 307


def test_get_channel_url():
    conda_main = "https://conda.anaconda.org/main"
    repo_main = "https://repo.anaconda.com/pkgs/main"
    example = "https://example.com"

    assert conda_utils.get_channel_url(conda_main) == yarl.URL(repo_main)
    assert conda_utils.get_channel_url(f"{conda_main}/") == yarl.URL(repo_main)
    assert conda_utils.get_channel_url(example) == yarl.URL(example)
