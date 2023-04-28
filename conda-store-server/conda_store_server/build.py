import datetime
import subprocess
import pathlib
import tempfile
import traceback

from typing import Dict, Union

import yaml

from conda_store_server import conda, orm, utils, schema, action


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


def set_build_completed(conda_store, build, logs):
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
        key=str(build.build_path(conda_store)),
    )
    conda_store.db.add(lockfile_build_artifact)
    conda_store.db.add(directory_build_artifact)

    build.environment.current_build = build
    build.environment.specification = build.specification
    conda_store.db.commit()


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
    conda_prefix.parent.mkdir(parents=True, exist_ok=True)

    environment_prefix = build.environment_path(conda_store)
    environment_prefix.parent.mkdir(parents=True, exist_ok=True)

    try:
        with utils.timer(conda_store.log, f"building {conda_prefix}"):
            context = action.action_solve_lockfile(
                conda_store.conda_command,
                specification=schema.CondaSpecification.parse_obj(
                    build.specification.spec
                ),
            )
            conda_lock_spec = context.result

            action.action_fetch_and_extract_conda_packages(
                conda_lock_spec=conda_lock_spec,
                pkgs_dir=conda.conda_root_package_dir(),
            )

            action.action_install_lockfile(
                conda_lock_spec=conda_lock_spec,
                conda_prefix=conda_prefix,
            )

            #     if build.specification.spec.get("variables") is not None:
            #         set_conda_environment_variables(
            #             pathlib.Path(conda_prefix),
            #             build.specification.spec["variables"],
            #         )

        utils.symlink(conda_prefix, environment_prefix)

        action.action_set_conda_prefix_permissions(
            conda_prefix=conda_prefix,
            permissions=conda_store.default_permissions,
            uid=conda_store.default_uid,
            gid=conda_store.default_gid,
        )

        action.action_add_conda_prefix_packages(
            db=conda_store.db,
            conda_prefix=conda_prefix,
            build_id=build.id,
        )

        context = action.action_get_conda_prefix_stats(conda_prefix)
        build.size = context.result["disk_usage"]

        set_build_completed(
            conda_store, build, b"Preparing transaction: Executing transaction:"
        )  # output.encode("utf-8"))
    except subprocess.CalledProcessError as e:
        conda_store.log.exception(e)
        set_build_failed(conda_store, build, e.output.encode("utf-8"))
        raise e
    except Exception as e:
        conda_store.log.exception(e)
        set_build_failed(conda_store, build, traceback.format_exc().encode("utf-8"))
        raise e


def solve_conda_environment(conda_store, solve):
    solve.started_on = datetime.datetime.utcnow()
    conda_store.db.commit()

    context = action.action_solve_lockfile(
        conda_command=conda_store.conda_command,
        specification=schema.CondaSpecification.parse_obj(solve.specification.spec),
        platforms=[conda.conda_platform()],
    )
    conda_lock_spec = context.result

    action.action_add_lockfile_packages(
        db=conda_store.db,
        conda_lock_spec=conda_lock_spec,
        solve_id=solve.id,
    )

    solve.ended_on = datetime.datetime.utcnow()
    conda_store.db.commit()


def build_conda_env_export(conda_store, build):
    conda_prefix = build.build_path(conda_store)

    context = action.action_generate_conda_export(
        conda_command=conda_store.conda_command, conda_prefix=conda_prefix
    )
    conda_prefix_export = yaml.dump(context.result).encode("utf-8")

    conda_store.storage.set(
        conda_store.db,
        build.id,
        build.conda_env_export_key,
        conda_prefix_export,
        content_type="text/yaml",
        artifact_type=schema.BuildArtifactType.YAML,
    )


def build_conda_pack(conda_store, build):
    conda_prefix = build.build_path(conda_store)

    conda_store.log.info(f"packaging archive of conda environment={conda_prefix}")
    with tempfile.TemporaryDirectory() as tmpdir:
        output_filename = pathlib.Path(tmpdir) / "environment.tar.gz"
        action.action_generate_conda_pack(
            conda_prefix=conda_prefix, output_filename=output_filename
        )
        conda_store.storage.fset(
            conda_store.db,
            build.id,
            build.conda_pack_key,
            output_filename,
            content_type="application/gzip",
            artifact_type=schema.BuildArtifactType.CONDA_PACK,
        )


def build_conda_docker(conda_store, build):
    conda_prefix = build.build_path(conda_store)

    context = action.action_generate_conda_docker(
        conda_prefix=conda_prefix,
        default_docker_image=utils.callable_or_value(
            conda_store.default_docker_base_image, None
        ),
        container_registry=conda_store.container_registry,
        output_image_name=build.specification.name,
        output_image_tag=build.build_key,
    )
    image = context.result

    if schema.BuildArtifactType.DOCKER_MANIFEST in conda_store.build_artifacts:
        conda_store.container_registry.store_image(conda_store, build, image)

    if schema.BuildArtifactType.CONTAINER_REGISTRY in conda_store.build_artifacts:
        conda_store.container_registry.push_image(conda_store, build, image)
