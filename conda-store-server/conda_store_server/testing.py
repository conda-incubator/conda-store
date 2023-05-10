import typing
import json
import uuid

from conda_store_server import schema, api, orm, conda


def seed_conda_store(
    conda_store,
    config: typing.Dict[str, typing.Dict[str, schema.CondaSpecification]] = {},
):
    for namespace_name in config:
        namespace = api.ensure_namespace(conda_store.db, name=namespace_name)
        for environment_name, specification in config[namespace_name].items():
            environment = api.ensure_environment(
                conda_store.db,
                name=specification.name,
                namespace_id=namespace.id,
            )
            specification = api.ensure_specification(conda_store.db, specification)
            build = api.create_build(conda_store.db, environment.id, specification.id)
            conda_store.db.commit()

            environment.current_build_id = build.id
            conda_store.db.commit()

            _create_build_artifacts(conda_store, build)
            _create_build_packages(conda_store, build)

            api.create_solve(conda_store.db, specification.id)
            conda_store.db.commit()


def _create_build_packages(conda_store, build: orm.Build):
    channel_name = conda.normalize_channel_name(
        conda_store.conda_channel_alias, "conda-forge"
    )
    channel = api.ensure_conda_channel(conda_store.db, channel_name)

    conda_package = orm.CondaPackage(
        name=f"madeup-{uuid.uuid4()}",
        version="1.2.3",
        channel_id=channel.id,
    )
    conda_store.db.add(conda_package)
    conda_store.db.commit()

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
    conda_store.db.add(conda_package_build)
    conda_store.db.commit()

    build.package_builds.append(conda_package_build)
    conda_store.db.commit()


def _create_build_artifacts(conda_store, build: orm.Build):
    conda_store.storage.set(
        conda_store.db,
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
    conda_store.db.add(directory_build_artifact)

    lockfile_build_artifact = orm.BuildArtifact(
        build_id=build.id, artifact_type=schema.BuildArtifactType.LOCKFILE, key=""
    )
    conda_store.db.add(lockfile_build_artifact)

    conda_store.storage.set(
        conda_store.db,
        build.id,
        build.conda_env_export_key,
        json.dumps(
            dict(name="testing", channels=["conda-forge"], dependencies=["numpy"])
        ).encode("utf-8"),
        content_type="text/yaml",
        artifact_type=schema.BuildArtifactType.YAML,
    )

    conda_store.storage.set(
        conda_store.db,
        build.id,
        build.conda_pack_key,
        b"testing-conda-package",
        content_type="application/gzip",
        artifact_type=schema.BuildArtifactType.CONDA_PACK,
    )

    # have not included docker at the moment
