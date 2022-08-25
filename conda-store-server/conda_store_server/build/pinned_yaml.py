import subprocess

import yaml

from conda_store_server import schema, api
from conda_store_server.build.base import CondaStoreBuilder
from conda_store_server.build.filesystem import FileSystemBuilder


class PinnedYAMLBuilder(CondaStoreBuilder):
    build_artifacts = [
        "YAML",
    ]

    depends_on = [
        FileSystemBuilder,
    ]

    def build_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        build = api.get_build(conda_store.db, build_id)
        build_conda_env_export(conda_store, build)

    def delete_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        for build_artifact in api.list_build_artifacts(
                db=conda_store.db,
                build_id=build_id,
                included_artifact_types=[artifact_type]
        ):
            conda_store.storage.delete(
                conda_store.db, build_artifact.build.id, build_artifact.key
            )


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
