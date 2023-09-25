import collections
import datetime
import json
import pathlib
import re
import subprocess
import tempfile
import traceback
import typing

import yaml
from conda_store_server import action, api, conda_utils, orm, schema, utils
from sqlalchemy.orm import Session


def append_to_logs(db: Session, conda_store, build, logs: typing.Union[str, bytes]):
    try:
        current_logs = conda_store.storage.get(build.log_key)
    except Exception:
        current_logs = b""

    if isinstance(logs, str):
        logs = logs.encode("utf-8")

    conda_store.storage.set(
        db,
        build.id,
        build.log_key,
        current_logs + logs,
        content_type="text/plain",
        artifact_type=schema.BuildArtifactType.LOGS,
    )


def set_build_started(db: Session, build: orm.Build):
    build.status = schema.BuildStatus.BUILDING
    build.started_on = datetime.datetime.utcnow()
    db.commit()


def set_build_failed(db: Session, build: orm.Build):
    build.status = schema.BuildStatus.FAILED
    build.ended_on = datetime.datetime.utcnow()
    db.commit()


def set_build_completed(db: Session, conda_store, build: orm.Build):
    build.status = schema.BuildStatus.COMPLETED
    build.ended_on = datetime.datetime.utcnow()

    directory_build_artifact = orm.BuildArtifact(
        build_id=build.id,
        artifact_type=schema.BuildArtifactType.DIRECTORY,
        key=str(build.build_path(conda_store)),
    )
    db.add(directory_build_artifact)

    build.environment.current_build = build
    build.environment.specification = build.specification
    db.commit()


def build_cleanup(db: Session, conda_store):
    """Walk through all builds in BUILDING state and check that they are actively running

    Build can get stuck in the building state due to worker
    spontaineously dying due to memory errors, killing container, etc.
    """
    inspect = conda_store.celery_app.control.inspect()
    active_tasks = inspect.active()
    if active_tasks is None:
        conda_store.log.warning(
            "build cleanup failed: celery broker does not support inspect"
        )
        return

    build_active_tasks = collections.defaultdict(list)
    for worker_name, tasks in active_tasks.items():
        for task in tasks:
            match = re.fullmatch("build-(\d+)-(.*)", str(task["id"]))
            if match:
                build_id, name = match.groups()
                build_active_tasks[build_id].append(task["name"])

    for build in api.list_builds(db, status=schema.BuildStatus.BUILDING):
        if str(build.id) not in build_active_tasks and build.started_on < (
            datetime.datetime.utcnow() - datetime.timedelta(seconds=5)
        ):
            conda_store.log.warning(
                f"marking build {build.id} as FAILED since stuck in BUILDING state and not present on workers"
            )
            append_to_logs(
                db,
                conda_store,
                build,
                """
Build marked as FAILED on cleanup due to being stuck in BUILDING state
and not present on workers. This happens for several reasons: from a
worker crash usually out of memory, worker was killed, or error in conda-store
""",
            )
            set_build_failed(db, build)


def build_conda_environment(db: Session, conda_store, build):
    """Build a conda environment with set uid/gid/and permissions and
    symlink the build to a named environment

    """
    set_build_started(db, build)
    append_to_logs(
        db,
        conda_store,
        build,
        f"starting build of conda environment {datetime.datetime.utcnow()} UTC\n",
    )

    settings = conda_store.get_settings(
        db=db,
        namespace=build.environment.namespace.name,
        environment_name=build.environment.name,
    )

    conda_prefix = build.build_path(conda_store)
    conda_prefix.parent.mkdir(parents=True, exist_ok=True)

    environment_prefix = build.environment_path(conda_store)
    environment_prefix.parent.mkdir(parents=True, exist_ok=True)

    try:
        with utils.timer(conda_store.log, f"building conda_prefix={conda_prefix}"):
            context = action.action_solve_lockfile(
                settings.conda_command,
                specification=schema.CondaSpecification.parse_obj(
                    build.specification.spec
                ),
                platforms=settings.conda_solve_platforms,
            )

            conda_store.storage.set(
                db,
                build.id,
                build.conda_lock_key,
                json.dumps(context.result, indent=4).encode("utf-8"),
                content_type="application/json",
                artifact_type=schema.BuildArtifactType.LOCKFILE,
            )

            append_to_logs(
                db,
                conda_store,
                build,
                "::group::action_solve_lockfile\n"
                + context.stdout.getvalue()
                + "\n::endgroup::\n",
            )
            conda_lock_spec = context.result

            context = action.action_fetch_and_extract_conda_packages(
                conda_lock_spec=conda_lock_spec,
                pkgs_dir=conda_utils.conda_root_package_dir(),
            )
            append_to_logs(
                db,
                conda_store,
                build,
                "::group::action_fetch_and_extract_conda_packages\n"
                + context.stdout.getvalue()
                + "\n::endgroup::\n",
            )

            context = action.action_install_lockfile(
                conda_lock_spec=conda_lock_spec,
                conda_prefix=conda_prefix,
            )
            append_to_logs(
                db,
                conda_store,
                build,
                "::group::action_install_lockfile\n"
                + context.stdout.getvalue()
                + "\n::endgroup::\n",
            )

        utils.symlink(conda_prefix, environment_prefix)

        action.action_set_conda_prefix_permissions(
            conda_prefix=conda_prefix,
            permissions=settings.default_permissions,
            uid=settings.default_uid,
            gid=settings.default_gid,
        )

        action.action_add_conda_prefix_packages(
            db=db,
            conda_prefix=conda_prefix,
            build_id=build.id,
        )

        context = action.action_get_conda_prefix_stats(conda_prefix)
        build.size = context.result["disk_usage"]

        set_build_completed(db, conda_store, build)
    except subprocess.CalledProcessError as e:
        conda_store.log.exception(e)
        append_to_logs(db, conda_store, build, e.output)
        set_build_failed(db, build)
        raise e
    except Exception as e:
        conda_store.log.exception(e)
        append_to_logs(db, conda_store, build, traceback.format_exc())
        set_build_failed(db, build)
        raise e


def solve_conda_environment(db: Session, conda_store, solve: orm.Solve):
    settings = conda_store.get_settings(db=db)

    solve.started_on = datetime.datetime.utcnow()
    db.commit()

    context = action.action_solve_lockfile(
        conda_command=settings.conda_command,
        specification=schema.CondaSpecification.parse_obj(solve.specification.spec),
        platforms=[conda_utils.conda_platform()],
    )
    conda_lock_spec = context.result

    action.action_add_lockfile_packages(
        db=db,
        conda_lock_spec=conda_lock_spec,
        solve_id=solve.id,
    )

    solve.ended_on = datetime.datetime.utcnow()
    db.commit()


def build_conda_env_export(db: Session, conda_store, build: orm.Build):
    conda_prefix = build.build_path(conda_store)
    settings = conda_store.get_settings(
        db=db,
        namespace=build.environment.namespace.name,
        environment_name=build.environment.name,
    )

    context = action.action_generate_conda_export(
        conda_command=settings.conda_command, conda_prefix=conda_prefix
    )
    append_to_logs(
        db,
        conda_store,
        build,
        "::group::action_generate_conda_export\n"
        + context.stdout.getvalue()
        + "\n::endgroup::\n",
    )

    conda_prefix_export = yaml.dump(context.result).encode("utf-8")

    conda_store.storage.set(
        db,
        build.id,
        build.conda_env_export_key,
        conda_prefix_export,
        content_type="text/yaml",
        artifact_type=schema.BuildArtifactType.YAML,
    )


def build_conda_pack(db: Session, conda_store, build: orm.Build):
    conda_prefix = build.build_path(conda_store)

    with utils.timer(
        conda_store.log, f"packaging archive of conda environment={conda_prefix}"
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_filename = pathlib.Path(tmpdir) / "environment.tar.gz"
            context = action.action_generate_conda_pack(
                conda_prefix=conda_prefix, output_filename=output_filename
            )
            append_to_logs(
                db,
                conda_store,
                build,
                "::group::action_generate_conda_pack\n"
                + context.stdout.getvalue()
                + "\n::endgroup::\n",
            )
            conda_store.storage.fset(
                db,
                build.id,
                build.conda_pack_key,
                output_filename,
                content_type="application/gzip",
                artifact_type=schema.BuildArtifactType.CONDA_PACK,
            )


def build_conda_docker(db: Session, conda_store, build: orm.Build):
    conda_prefix = build.build_path(conda_store)
    settings = conda_store.get_settings(
        db=db,
        namespace=build.environment.namespace.name,
        environment_name=build.environment.name,
    )

    try:
        with utils.timer(
            conda_store.log,
            f"packaging docker image of conda environment={conda_prefix}",
        ):
            context = action.action_generate_conda_docker(
                conda_prefix=conda_prefix,
                default_docker_image=utils.callable_or_value(
                    settings.default_docker_base_image, None
                ),
                container_registry=conda_store.container_registry,
                output_image_name=build.specification.name,
                output_image_tag=build.build_key,
            )
            append_to_logs(
                db,
                conda_store,
                build,
                "::group::action_generate_conda_docker\n"
                + context.stdout.getvalue()
                + "\n::endgroup::\n",
            )

            image = context.result

            if schema.BuildArtifactType.DOCKER_MANIFEST in settings.build_artifacts:
                conda_store.container_registry.store_image(
                    db, conda_store, build, image
                )

            if schema.BuildArtifactType.CONTAINER_REGISTRY in settings.build_artifacts:
                conda_store.container_registry.push_image(db, build, image)
    except Exception as e:
        conda_store.log.exception(e)
        append_to_logs(db, conda_store, build, traceback.format_exc())
        raise e
