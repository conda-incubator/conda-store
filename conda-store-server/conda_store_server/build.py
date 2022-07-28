import datetime
import gzip
import hashlib
import os
import stat
import subprocess
import tempfile
import traceback

import filelock
import yaml

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
    for package in packages:
        channel = package["channel_id"]
        if channel == "https://conda.anaconda.org/pypi":
            # ignore pypi package for now
            continue

        channel_orm = api.get_conda_channel(conda_store.db, channel)
        if channel_orm is None:
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
        build.packages.append(_package)

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


def build_conda_environment(conda_store, build):
    """Build a conda environment with set uid/gid/and permissions and
    symlink the build to a named environment

    """
    set_build_started(conda_store, build)

    conda_prefix = build.build_path(conda_store)
    os.makedirs(os.path.dirname(conda_prefix), exist_ok=True)

    environment_prefix = build.environment_path(conda_store)
    os.makedirs(os.path.dirname(environment_prefix), exist_ok=True)

    conda_store.log.info(f"building conda environment={conda_prefix}")

    try:
        with utils.timer(conda_store.log, f"building {conda_prefix}"):
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_environment_filename = os.path.join(tmpdir, "environment.yaml")
                with open(tmp_environment_filename, "w") as f:
                    yaml.dump(build.specification.spec, f)
                    if conda_store.serialize_builds:
                        with filelock.FileLock(
                            os.path.join(tempfile.tempdir, "conda-store.lock")
                        ):
                            output = build_environment(
                                conda_store.conda_command,
                                tmp_environment_filename,
                                conda_prefix,
                            )
                    else:
                        output = build_environment(
                            conda_store.conda_command,
                            tmp_environment_filename,
                            conda_prefix,
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
        find_user_conda,
        conda_info,
        precs_from_environment_prefix,
        fetch_precs,
    )

    conda_prefix = build.build_path(conda_store)

    conda_store.log.info(f"creating docker archive of conda environment={conda_prefix}")

    user_conda = find_user_conda()
    info = conda_info(user_conda)
    download_dir = info["pkgs_dirs"][0]
    precs = precs_from_environment_prefix(conda_prefix, download_dir, user_conda)
    records = fetch_precs(download_dir, precs)
    image = build_docker_environment_image(
        base_image=conda_store.default_docker_base_image,
        output_image=f"{build.specification.name}:{build.build_key}",
        records=records,
        default_prefix=info["env_vars"]["CONDA_ROOT"],
        download_dir=download_dir,
        user_conda=user_conda,
        channels_remap=info.get("channels_remap", []),
        layering_strategy="layered",
    )

    # https://docs.docker.com/registry/spec/manifest-v2-2/#example-image-manifest
    docker_manifest = schema.DockerManifest.construct()
    docker_config = schema.DockerConfig.construct(
        config=schema.DockerConfigConfig(),
        container_config=schema.DockerConfigConfig(),
        rootfs=schema.DockerConfigRootFS(),
    )

    for layer in image.layers:
        # https://github.com/google/nixery/pull/64#issuecomment-541019077
        # docker manifest expects compressed hash while configuration file
        # expects uncompressed hash -- good luck finding this detail in docs :)
        content_uncompressed_hash = hashlib.sha256(layer.content).hexdigest()
        content_compressed = gzip.compress(layer.content)
        content_compressed_hash = hashlib.sha256(content_compressed).hexdigest()
        conda_store.storage.set(
            conda_store.db,
            build.id,
            build.docker_blob_key(content_compressed_hash),
            content_compressed,
            content_type="application/gzip",
            artifact_type=schema.BuildArtifactType.DOCKER_BLOB,
        )

        docker_layer = schema.DockerManifestLayer(
            size=len(content_compressed), digest=f"sha256:{content_compressed_hash}"
        )
        docker_manifest.layers.append(docker_layer)

        docker_config_history = schema.DockerConfigHistory()
        docker_config.history.append(docker_config_history)

        docker_config.rootfs.diff_ids.append(f"sha256:{content_uncompressed_hash}")

    docker_config_content = docker_config.json().encode("utf-8")
    docker_config_hash = hashlib.sha256(docker_config_content).hexdigest()
    docker_manifest.config = schema.DockerManifestConfig(
        size=len(docker_config_content), digest=f"sha256:{docker_config_hash}"
    )
    docker_manifest_content = docker_manifest.json().encode("utf-8")
    docker_manifest_hash = hashlib.sha256(docker_manifest_content).hexdigest()

    conda_store.storage.set(
        conda_store.db,
        build.id,
        build.docker_blob_key(docker_config_hash),
        docker_config_content,
        content_type="application/vnd.docker.container.image.v1+json",
        artifact_type=schema.BuildArtifactType.DOCKER_BLOB,
    )

    # docker likes to have a sha256 key version of the manifest this
    # is sort of hack to avoid having to figure out which sha256
    # refers to which manifest.
    conda_store.storage.set(
        conda_store.db,
        build.id,
        f"docker/manifest/sha256:{docker_manifest_hash}",
        docker_manifest_content,
        content_type="application/vnd.docker.distribution.manifest.v2+json",
        artifact_type=schema.BuildArtifactType.DOCKER_BLOB,
    )

    conda_store.storage.set(
        conda_store.db,
        build.id,
        build.docker_manifest_key,
        docker_manifest_content,
        content_type="application/vnd.docker.distribution.manifest.v2+json",
        artifact_type=schema.BuildArtifactType.DOCKER_MANIFEST,
    )

    conda_store.log.info(
        f"built docker image: {image.name}:{image.tag} layers={len(image.layers)}"
    )
