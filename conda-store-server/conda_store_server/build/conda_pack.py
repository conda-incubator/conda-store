import tempfile
import os

from conda_store_server import schema, conda, api
from conda_store_server.build.base import CondaStoreBuilder
from conda_store_server.build.solve import FileSystemBuilder


class CondaPackBuilder(CondaStoreBuilder):
    build_artifacts = [
        "CONDA_PACK",
    ]

    depends_on = [
        FileSystemBuilder,
    ]

    def build_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        build = api.get_build(conda_store.db, build_id)
        if artifact_type == "CONDA_PACK":
            build_conda_pack(conda_store, build)

    def delete_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: int):
        for build_artifact in api.list_build_artifacts(
                db=conda_store.db,
                build_id=build_id,
                included_artifact_types=[artifact_type]
        ):
            conda_store.storage.delete(
                conda_store.db, build_artifact.build.id, build_artifact.key
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
