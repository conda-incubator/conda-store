# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

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
from filelock import FileLock
from sqlalchemy.orm import Session

from conda_store_server import api
from conda_store_server._internal import action, conda_utils, orm, schema, utils
from conda_store_server.exception import BuildPathError
from conda_store_server.plugins import plugin_context


class LoggedStream:
    """Allows writing to storage via logging.StreamHandler"""

    def __init__(self, db, conda_store, build, prefix=None):
        self.db = db
        self.conda_store = conda_store
        self.build = build
        self.prefix = prefix

    def write(self, b, /):
        for line in b.split("\n"):
            # Skips empty lines
            if not line:
                continue
            if self.prefix is not None:
                line = self.prefix + line
            append_to_logs(self.db, self.conda_store, self.build, line + "\n")

    def flush(self):
        pass


def append_to_logs(db: Session, conda_store, build, logs: typing.Union[str, bytes]):
    # For instance, with local storage, this involves reading from and writing
    # to a file. Locking here prevents a race condition when multiple tasks
    # attempt to write to a shared resource, which is the log
    with FileLock(f"{build.build_path(conda_store)}.log.lock"):
        try:
            current_logs = conda_store.storage.get(build.log_key)
        except Exception:
            current_logs = b""

        if current_logs is None:
            current_logs = b""

        if isinstance(logs, str):
            logs = logs.encode("utf-8")
        elif logs is None:
            logs = b""

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


def set_build_failed(
    db: Session, build: orm.Build, status_info: typing.Optional[str] = None
):
    build.status = schema.BuildStatus.FAILED
    build.status_info = status_info
    build.ended_on = datetime.datetime.utcnow()
    db.commit()


def set_build_canceled(
    db: Session, build: orm.Build, status_info: typing.Optional[str] = None
):
    build.status = schema.BuildStatus.CANCELED
    build.status_info = status_info
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


def build_cleanup(
    db: Session,
    conda_store,
    build_ids: typing.List[str] = None,
    reason: str = None,
    is_canceled: bool = False,
):
    """Walk through all builds in BUILDING state and check that they are actively running

    Build can get stuck in the building state due to worker
    spontaineously dying due to memory errors, killing container, etc.
    """
    status = "CANCELED" if is_canceled else "FAILED"
    reason = (
        reason
        or f"""
Build marked as {status} on cleanup due to being stuck in BUILDING state
and not present on workers. This happens for several reasons: build is
canceled, a worker crash from out of memory errors, worker was killed,
or error in conda-store
"""
    )

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
            match = re.fullmatch(r"build-(\d+)-(.*)", str(task["id"]))
            if match:
                build_id, name = match.groups()
                build_active_tasks[build_id].append(task["name"])

    if build_ids:
        builds = [api.get_build(db, build_id) for build_id in build_ids]
    else:
        builds = api.list_builds(db, status=schema.BuildStatus.BUILDING)

    for build in builds:
        if (
            build.status == schema.BuildStatus.BUILDING
            and str(build.id) not in build_active_tasks
            and (
                build.started_on
                < (datetime.datetime.utcnow() - datetime.timedelta(seconds=5))
            )
        ):
            conda_store.log.warning(
                f"marking build {build.id} as {status} since stuck in BUILDING state and not present on workers"
            )
            append_to_logs(
                db,
                conda_store,
                build,
                reason,
            )
            if is_canceled:
                set_build_canceled(db, build)
            else:
                set_build_failed(db, build)


def build_conda_environment(db: Session, conda_store, build):
    """Build a conda environment with set uid/gid/and permissions and
    symlink the build to a named environment

    """
    try:
        set_build_started(db, build)
        # Note: even append_to_logs can fail due to filename size limit, so
        # check build_path length first
        conda_prefix = build.build_path(conda_store)
        append_to_logs(
            db,
            conda_store,
            build,
            f"starting build of conda environment {datetime.datetime.utcnow()} UTC\n",
        )

        settings = conda_store.get_settings(
            namespace=build.environment.namespace.name,
            environment_name=build.environment.name,
        )

        conda_prefix.parent.mkdir(parents=True, exist_ok=True)

        environment_prefix = build.environment_path(conda_store)
        if environment_prefix is not None:
            environment_prefix.parent.mkdir(parents=True, exist_ok=True)

        is_lockfile = build.specification.is_lockfile

        with utils.timer(conda_store.log, f"building conda_prefix={conda_prefix}"):
            if is_lockfile:
                context = action.action_save_lockfile(
                    specification=schema.LockfileSpecification.model_validate(
                        build.specification.spec
                    ),
                    stdout=LoggedStream(
                        db=db,
                        conda_store=conda_store,
                        build=build,
                        prefix="action_save_lockfile: ",
                    ),
                )
                conda_lock_spec = context.result
            else:
                lock_backend, locker = conda_store.lock_plugin()
                conda_lock_spec = locker.lock_environment(
                    spec=schema.CondaSpecification.model_validate(
                        build.specification.spec
                    ),
                    platforms=settings.conda_solve_platforms,
                    context=plugin_context.PluginContext(
                        conda_store=conda_store,
                        stdout=LoggedStream(
                            db=db,
                            conda_store=conda_store,
                            build=build,
                            prefix=f"plugin-{lock_backend}: ",
                        ),
                    ),
                )

            conda_store.storage.set(
                db,
                build.id,
                build.conda_lock_key,
                json.dumps(
                    conda_lock_spec, indent=4, cls=utils.CustomJSONEncoder
                ).encode("utf-8"),
                content_type="application/json",
                artifact_type=schema.BuildArtifactType.LOCKFILE,
            )

            context = action.action_fetch_and_extract_conda_packages(
                conda_lock_spec=conda_lock_spec,
                pkgs_dir=conda_utils.conda_root_package_dir(),
                stdout=LoggedStream(
                    db=db,
                    conda_store=conda_store,
                    build=build,
                    prefix="action_fetch_and_extract_conda_packages: ",
                ),
            )

            context = action.action_install_lockfile(
                conda_lock_spec=conda_lock_spec,
                conda_prefix=conda_prefix,
                stdout=LoggedStream(
                    db=db,
                    conda_store=conda_store,
                    build=build,
                    prefix="action_install_lockfile: ",
                ),
            )

        if environment_prefix is not None:
            utils.symlink(conda_prefix, environment_prefix)

        action.action_set_conda_prefix_permissions(
            conda_prefix=conda_prefix,
            permissions=settings.default_permissions,
            uid=settings.default_uid,
            gid=settings.default_gid,
            stdout=LoggedStream(
                db=db,
                conda_store=conda_store,
                build=build,
                prefix="action_set_conda_prefix_permissions: ",
            ),
        )

        action.action_add_conda_prefix_packages(
            db=db,
            conda_prefix=conda_prefix,
            build_id=build.id,
            stdout=LoggedStream(
                db=db,
                conda_store=conda_store,
                build=build,
                prefix="action_add_conda_prefix_packages: ",
            ),
        )

        context = action.action_get_conda_prefix_stats(
            conda_prefix,
            stdout=LoggedStream(
                db=db,
                conda_store=conda_store,
                build=build,
                prefix="action_get_conda_prefix_stats: ",
            ),
        )
        build.size = context.result["disk_usage"]

        set_build_completed(db, conda_store, build)
    # Always mark build as failed first since other functions may throw an
    # exception
    except subprocess.CalledProcessError as e:
        set_build_failed(db, build)
        conda_store.log.exception(e)
        append_to_logs(db, conda_store, build, e.output)
        raise e
    except BuildPathError as e:
        # Provide status_info, which will be exposed to the user, ONLY in this
        # case because the error message doesn't expose sensitive information
        set_build_failed(db, build, status_info=e.message)
        conda_store.log.exception(e)
        append_to_logs(db, conda_store, build, traceback.format_exc())
        raise e
    except Exception as e:
        set_build_failed(db, build)
        conda_store.log.exception(e)
        append_to_logs(db, conda_store, build, traceback.format_exc())
        raise e


def solve_conda_environment(db: Session, conda_store, solve: orm.Solve):
    solve.started_on = datetime.datetime.utcnow()
    db.commit()

    _, locker = conda_store.lock_plugin()
    conda_lock_spec = locker.lock_environment(
        context=plugin_context.PluginContext(conda_store=conda_store),
        spec=schema.CondaSpecification.model_validate(solve.specification.spec),
        platforms=[conda_utils.conda_platform()],
    )

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
        namespace=build.environment.namespace.name,
        environment_name=build.environment.name,
    )

    context = action.action_generate_conda_export(
        conda_command=settings.conda_command,
        conda_prefix=conda_prefix,
        stdout=LoggedStream(
            db=db,
            conda_store=conda_store,
            build=build,
            prefix="action_generate_conda_export: ",
        ),
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
            action.action_generate_conda_pack(
                conda_prefix=conda_prefix,
                output_filename=output_filename,
                stdout=LoggedStream(
                    db=db,
                    conda_store=conda_store,
                    build=build,
                    prefix="action_generate_conda_pack: ",
                ),
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
    import warnings

    warnings.warn(
        "Generating Docker images is not supported and will be removed "
        "in a future release"
    )
    return


def build_constructor_installer(db: Session, conda_store, build: orm.Build):
    conda_prefix = build.build_path(conda_store)

    settings = conda_store.get_settings(
        namespace=build.environment.namespace.name,
        environment_name=build.environment.name,
    )

    with utils.timer(
        conda_store.log, f"creating installer for conda environment={conda_prefix}"
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            is_lockfile = build.specification.is_lockfile

            if is_lockfile:
                specification = schema.LockfileSpecification.model_validate(
                    build.specification.spec
                )
            else:
                try:
                    # Tries to use the lockfile if it's available since it has
                    # pinned dependencies. This code is wrapped into try/except
                    # because the lockfile lookup might fail if the file is not
                    # in external storage or on disk, or if parsing fails
                    specification = schema.LockfileSpecification.model_validate(
                        {
                            "name": build.specification.name,
                            "lockfile": json.loads(
                                conda_store.storage.get(build.conda_lock_key)
                            ),
                        }
                    )
                    is_lockfile = True
                except Exception as e:
                    conda_store.log.warning(
                        "Exception while obtaining lockfile, using specification",
                        exc_info=e,
                    )
                    specification = schema.CondaSpecification.model_validate(
                        build.specification.spec
                    )

            context = action.action_generate_constructor_installer(
                conda_command=settings.conda_command,
                specification=specification,
                installer_dir=pathlib.Path(tmpdir),
                version=build.build_key,
                stdout=LoggedStream(
                    db=db,
                    conda_store=conda_store,
                    build=build,
                    prefix="action_generate_constructor_installer: ",
                ),
                is_lockfile=is_lockfile,
            )
            output_filename = context.result
            if output_filename is None:
                return
            conda_store.storage.fset(
                db,
                build.id,
                build.constructor_installer_key,
                output_filename,
                content_type="application/octet-stream",
                artifact_type=schema.BuildArtifactType.CONSTRUCTOR_INSTALLER,
            )
