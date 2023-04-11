import datetime
import os
import stat
import subprocess
import pathlib
import tempfile
import traceback
import shutil

from typing import Dict, Union

import filelock
import yaml
import conda_package_handling.api
import conda_package_streaming.url

from conda_store_server import api, conda, orm, utils, schema


def set_build_started(conda_store, build):
    build.status = schema.BuildStatus.BUILDING
    build.started_on = datetime.datetime.utcnow()
    conda_store.db.commit()


def set_build_failed(conda_store, build, logs):
    conda_store.storage.set(
        conda_store.db,
        build.id,
        build.log_key,
        logs,
        content_type="text/plain",
        artifact_type=schema.BuildArtifactType.LOGS,
    )
    build.status = schema.BuildStatus.FAILED
    build.ended_on = datetime.datetime.utcnow()
    conda_store.db.commit()


def set_build_completed(conda_store, build, logs, packages):
    package_keys = [
        "channel_id",
        "license",
        "license_family",
        "name",
        "version",
        "summary",
        "description",
    ]
    package_build_keys = [
        "build",
        "build_number",
        "constrains",
        "depends",
        "md5",
        "sha256",
        "size",
        "subdir",
        "timestamp",
    ]

    for package in packages:

        channel = package["channel_id"]
        if channel == "https://conda.anaconda.org/pypi":
            # ignore pypi package for now
            continue

        channel_orm = api.get_conda_channel(conda_store.db, channel)
        if channel_orm is None:
            # Empty list for conda_allowed_channels allows any channel ( PR #358 )
            if len(conda_store.conda_allowed_channels) == 0:
                channel_orm = api.create_conda_channel(conda_store.db, channel)
                conda_store.db.commit()
            else:
                raise ValueError(
                    f"channel url={channel} not recognized in conda-store channel database"
                )
        package["channel_id"] = channel_orm.id

        # Retrieve the package from the DB if it already exists
        _package = (
            conda_store.db.query(orm.CondaPackage)
            .filter(orm.CondaPackage.channel_id == package["channel_id"])
            .filter(orm.CondaPackage.name == package["name"])
            .filter(orm.CondaPackage.version == package["version"])
            .first()
        )

        # If it doesn't exist, let's create it in DB
        if _package is None:
            package_dict = {k: package[k] for k in package_keys}
            _package = orm.CondaPackage(**package_dict)
            conda_store.db.add(_package)

        # Retrieve the build for this pacakge, if it already exists
        _package_build = (
            conda_store.db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.package == _package)
            .filter(orm.CondaPackageBuild.md5 == package["md5"])
            .first()
        )

        # If it doesn't exist, let's create it in DB
        if _package_build is None:
            package_build_dict = {k: package[k] for k in package_build_keys}
            # Attach the package_build to its package
            package_build_dict["package_id"] = _package.id
            _package_build = orm.CondaPackageBuild(**package_build_dict)
            conda_store.db.add(_package_build)

        build.package_builds.append(_package_build)
        conda_store.db.commit()

    conda_store.storage.set(
        conda_store.db,
        build.id,
        build.log_key,
        logs,
        content_type="text/plain",
        artifact_type=schema.BuildArtifactType.LOGS,
    )
    build.status = schema.BuildStatus.COMPLETED
    build.ended_on = datetime.datetime.utcnow()

    # add records for lockfile and directory build artifacts
    lockfile_build_artifact = orm.BuildArtifact(
        build_id=build.id, artifact_type=schema.BuildArtifactType.LOCKFILE, key=""
    )
    directory_build_artifact = orm.BuildArtifact(
        build_id=build.id,
        artifact_type=schema.BuildArtifactType.DIRECTORY,
        key=build.build_path(conda_store),
    )
    conda_store.db.add(lockfile_build_artifact)
    conda_store.db.add(directory_build_artifact)

    environment = (
        conda_store.db.query(orm.Environment)
        .filter(orm.Environment.name == build.specification.name)
        .first()
    )
    environment.current_build = build
    environment.specification = build.specification
    conda_store.db.commit()


def build_environment(conda_command, environment_filename, conda_prefix):
    return subprocess.check_output(
        [
            conda_command,
            "env",
            "create",
            "-p",
            conda_prefix,
            "-f",
            str(environment_filename),
        ],
        stderr=subprocess.STDOUT,
        encoding="utf-8",
    )


def build_lock_environment(lock_filename: pathlib.Path, conda_prefix: pathlib.Path):
    return subprocess.check_output(
        ["conda-lock", "install", "--prefix", str(conda_prefix), str(lock_filename)],
        stderr=subprocess.STDOUT,
        encoding="utf-8",
    )


def fetch_and_extract_packages(conda_store, conda_lock_filename: pathlib.Path):
    """Download packages from a conda-lock specification using filelocks"""
    prefix: pathlib.Path = conda.conda_root_package_dir()

    try:
        prefix.exists()
    except FileNotFoundError as e:
        conda_store.log.error(
            f"The conda prefix {prefix} does not exist. Traceback: {e}"
        )

    with conda_lock_filename.open() as f:
        spec = yaml.safe_load(f)

    packages_searched = 1
    total_packages = len(spec["package"])

    for package in spec["package"]:
        packages_searched += 1
        if package["manager"] == "conda":
            url: str = package["url"]
            filepath: pathlib.Path = prefix.joinpath(
                pathlib.Path(url.split("/")[-1:][0])
            )
            count_message = f"{packages_searched} of {total_packages}"
            with filelock.FileLock(f"{str(filepath)}.lock"):

                if filepath.exists():
                    conda_store.log.info(f"SKIPPING {filepath.name} | FILE EXISTS")
                else:
                    conda_store.log.info(f"DOWNLOAD {filepath.name} | {count_message}")
                    (
                        filename,
                        conda_package_stream,
                    ) = conda_package_streaming.url.conda_reader_for_url(url)
                    with filepath.open("wb") as f:
                        shutil.copyfileobj(conda_package_stream, f)

                    conda_package_handling.api.extract(str(filepath))


def solve_lock_environment(
    conda_command: str, environment_filename: pathlib.Path, lock_filename: pathlib.Path
):
    from conda_lock.conda_lock import run_lock
    from conda_store_server.conda import conda_platform

    run_lock(
        environment_files=[environment_filename],
        platforms=[conda_platform()],
        lockfile_path=lock_filename,
        conda_exe=conda_command,
    )


def set_conda_environment_variables(
    conda_prefix: pathlib.Path, environment_variables: Dict[str, Union[str, int]]
):
    """Takes an input of the conda prefix and the, variables defined in the environment yaml
    specification. Then, generates the files neccesary to "activate" these when an environment
    is activated.
    """
    for item in ("activate", "deactivate"):
        folderpath = conda_prefix.joinpath("etc", "conda", f"{item}.d")
        folderpath.mkdir(parents=True, exist_ok=False)
        env_vars_file = folderpath.joinpath("env_vars.sh")
        env_vars_file.touch()
        with open(env_vars_file, "w") as f:
            f.write("#!/bin/bash\n")
            if item == "activate":
                for key in environment_variables:
                    f.write(f"export {key}={environment_variables[key]}\n")
            elif item == "deactivate":
                for key in environment_variables.keys():
                    f.write(f"unset {key}\n")
    return


def build_conda_environment(conda_store, build):
    """Build a conda environment with set uid/gid/and permissions and
    symlink the build to a named environment

    """
    set_build_started(conda_store, build)

    conda_prefix = build.build_path(conda_store)
    os.makedirs(os.path.dirname(conda_prefix), exist_ok=True)

    environment_prefix = build.environment_path(conda_store)
    os.makedirs(os.path.dirname(environment_prefix), exist_ok=True)

    try:
        with utils.timer(conda_store.log, f"building {conda_prefix}"):
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_environment_filename = os.path.join(tmpdir, "environment.yaml")
                tmp_lock_filename = os.path.join(tmpdir, "conda-lock.yml")

                with open(tmp_environment_filename, "w") as f:
                    yaml.dump(build.specification.spec, f)

                solve_lock_environment(
                    conda_store.conda_command,
                    pathlib.Path(tmp_environment_filename),
                    pathlib.Path(tmp_lock_filename),
                )

                fetch_and_extract_packages(conda_store, pathlib.Path(tmp_lock_filename))

                output = build_lock_environment(
                    pathlib.Path(tmp_lock_filename),
                    conda_prefix,
                )

                if build.specification.spec.get("variables") is not None:
                    set_conda_environment_variables(
                        pathlib.Path(conda_prefix),
                        build.specification.spec["variables"],
                    )

        utils.symlink(conda_prefix, environment_prefix)

        # modify permissions, uid, gid if they do not match
        stat_info = os.stat(conda_prefix)
        permissions = conda_store.default_permissions
        uid = conda_store.default_uid
        gid = conda_store.default_gid

        if permissions is not None and oct(stat.S_IMODE(stat_info.st_mode))[-3:] != str(
            permissions
        ):
            conda_store.log.info(
                f"modifying permissions of {conda_prefix} to permissions={permissions}"
            )
            with utils.timer(conda_store.log, f"chmod of {conda_prefix}"):
                utils.chmod(conda_prefix, permissions)

        if (
            uid is not None
            and gid is not None
            and (str(uid) != str(stat_info.st_uid) or str(gid) != str(stat_info.st_gid))
        ):
            conda_store.log.info(
                f"modifying permissions of {conda_prefix} to uid={uid} and gid={gid}"
            )
            with utils.timer(conda_store.log, f"chown of {conda_prefix}"):
                utils.chown(conda_prefix, uid, gid)

        packages = conda.conda_prefix_packages(conda_prefix)
        build.size = utils.disk_usage(conda_prefix)

        set_build_completed(conda_store, build, output.encode("utf-8"), packages)
    except subprocess.CalledProcessError as e:
        conda_store.log.exception(e)
        set_build_failed(conda_store, build, e.output.encode("utf-8"))
        raise e
    except Exception as e:
        conda_store.log.exception(e)
        set_build_failed(conda_store, build, traceback.format_exc().encode("utf-8"))
        raise e


def solve_conda_environment(conda_store, solve):
    from conda_store_server.conda import conda_lock

    try:
        solve.started_on = datetime.datetime.utcnow()
        conda_store.db.commit()

        specification = schema.CondaSpecification.parse_obj(solve.specification.spec)
        packages = conda_lock(specification, conda_store.conda_command)

        for package in packages["conda"]:
            channel = package["channel_id"]
            if channel == "https://conda.anaconda.org/pypi":
                # ignore pypi package for now
                continue

            channel_orm = api.get_conda_channel(conda_store.db, channel)
            if channel_orm is None:
                # Empty list for conda_allowed_channels allows any channel ( PR #358 )
                if len(conda_store.conda_allowed_channels) == 0:
                    channel_orm = api.create_conda_channel(conda_store.db, channel)
                    conda_store.db.commit()
                else:
                    raise ValueError(
                        f"channel url={channel} not recognized in conda-store channel database"
                    )
            package["channel_id"] = channel_orm.id

            _package = (
                conda_store.db.query(orm.CondaPackage)
                .filter(orm.CondaPackage.md5 == package["md5"])
                .filter(orm.CondaPackage.channel_id == package["channel_id"])
                .first()
            )

            if _package is None:
                _package = orm.CondaPackage(**package)
                conda_store.db.add(_package)
            solve.packages.append(_package)
        solve.ended_on = datetime.datetime.utcnow()
        conda_store.db.commit()
    except Exception as e:
        print("Task failed!!!!!!!!!!!", str(e))
        raise e


def build_conda_env_export(conda_store, build):
    conda_prefix = build.build_path(conda_store)

    output = subprocess.check_output(
        [conda_store.conda_command, "env", "export", "-p", conda_prefix]
    )

    parsed = yaml.safe_load(output)
    if "dependencies" not in parsed:
        raise ValueError(f"conda env export` did not produce valid YAML:\n{output}")

    conda_store.storage.set(
        conda_store.db,
        build.id,
        build.conda_env_export_key,
        output,
        content_type="text/yaml",
        artifact_type=schema.BuildArtifactType.YAML,
    )


def build_conda_pack(conda_store, build):
    conda_prefix = build.build_path(conda_store)

    conda_store.log.info(f"packaging archive of conda environment={conda_prefix}")
    with tempfile.TemporaryDirectory() as tmpdir:
        output_filename = os.path.join(tmpdir, "environment.tar.gz")
        conda.conda_pack(prefix=conda_prefix, output=output_filename)
        conda_store.storage.fset(
            conda_store.db,
            build.id,
            build.conda_pack_key,
            output_filename,
            content_type="application/gzip",
            artifact_type=schema.BuildArtifactType.CONDA_PACK,
        )


def build_conda_docker(conda_store, build):
    from conda_docker.conda import (
        build_docker_environment_image,
        conda_info,
        fetch_precs,
        find_user_conda,
        precs_from_environment_prefix,
    )

    conda_prefix = build.build_path(conda_store)

    conda_store.log.info(f"creating docker archive of conda environment={conda_prefix}")

    user_conda = find_user_conda()
    info = conda_info(user_conda)
    download_dir = info["pkgs_dirs"][0]
    precs = precs_from_environment_prefix(conda_prefix, download_dir, user_conda)
    records = fetch_precs(download_dir, precs)
    base_image = conda_store.container_registry.pull_image(
        utils.callable_or_value(conda_store.default_docker_base_image, build)
    )
    image = build_docker_environment_image(
        base_image=base_image,
        output_image=f"{build.specification.name}:{build.build_key}",
        records=records,
        default_prefix=info["env_vars"]["CONDA_ROOT"],
        download_dir=download_dir,
        user_conda=user_conda,
        channels_remap=info.get("channels_remap", []),
        layering_strategy="layered",
    )

    if schema.BuildArtifactType.DOCKER_MANIFEST in conda_store.build_artifacts:
        conda_store.container_registry.store_image(conda_store, build, image)

    if schema.BuildArtifactType.CONTAINER_REGISTRY in conda_store.build_artifacts:
        conda_store.container_registry.push_image(conda_store, build, image)
