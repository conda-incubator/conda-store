import json
import typing
import uuid

from conda_store_server import api, conda_utils, orm, schema
from sqlalchemy.orm import Session


def seed_conda_store(
    db: Session,
    conda_store,
    config: typing.Dict[str, typing.Dict[str, schema.CondaSpecification]] = {},
):
    for namespace_name in config:
        namespace = api.ensure_namespace(db, name=namespace_name)
        for environment_name, specification in config[namespace_name].items():
            environment = api.ensure_environment(
                db,
                name=specification.name,
                namespace_id=namespace.id,
            )
            specification = api.ensure_specification(db, specification)
            build = api.create_build(db, environment.id, specification.id)
            db.commit()

            environment.current_build_id = build.id
            db.commit()

            _create_build_artifacts(db, conda_store, build)
            _create_build_packages(db, conda_store, build)

            api.create_solve(db, specification.id)
            db.commit()


def _create_build_packages(db: Session, conda_store, build: orm.Build):
    channel_name = conda_utils.normalize_channel_name(
        conda_store.conda_channel_alias, "conda-forge"
    )
    channel = api.ensure_conda_channel(db, channel_name)

    conda_package = orm.CondaPackage(
        name=f"madeup-{uuid.uuid4()}",
        version="1.2.3",
        channel_id=channel.id,
    )
    db.add(conda_package)
    db.commit()

    conda_package_build = orm.CondaPackageBuild(
        package_id=conda_package.id,
        build="fakebuild",
        build_number=1,
        constrains=[],
        depends=[],
        md5=str(uuid.uuid4()),
        sha256=str(uuid.uuid4()),
        size=123456,
        subdir="noarch",
        timestamp=12345667,
    )
    db.add(conda_package_build)
    db.commit()

    build.package_builds.append(conda_package_build)
    db.commit()


def _create_build_artifacts(db: Session, conda_store, build: orm.Build):
    conda_store.storage.set(
        db,
        build.id,
        build.log_key,
        b"fake logs",
        content_type="text/plain",
        artifact_type=schema.BuildArtifactType.LOGS,
    )

    directory_build_artifact = orm.BuildArtifact(
        build_id=build.id,
        artifact_type=schema.BuildArtifactType.DIRECTORY,
        key=str(build.build_path(conda_store)),
    )
    db.add(directory_build_artifact)

    lockfile_build_artifact = orm.BuildArtifact(
        build_id=build.id, artifact_type=schema.BuildArtifactType.LOCKFILE, key=""
    )
    db.add(lockfile_build_artifact)

    conda_store.storage.set(
        db,
        build.id,
        build.conda_env_export_key,
        json.dumps(
            dict(name="testing", channels=["conda-forge"], dependencies=["numpy"])
        ).encode("utf-8"),
        content_type="text/yaml",
        artifact_type=schema.BuildArtifactType.YAML,
    )

    conda_store.storage.set(
        db,
        build.id,
        build.conda_pack_key,
        b"testing-conda-package",
        content_type="application/gzip",
        artifact_type=schema.BuildArtifactType.CONDA_PACK,
    )

    # have not included docker at the moment
