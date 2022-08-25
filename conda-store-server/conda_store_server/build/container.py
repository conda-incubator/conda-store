from traitlets import Union, Unicode, Callable

from conda_store_server import schema, utils, api
from conda_store_server.build.base import CondaStoreBuilder
from conda_store_server.build.solve import FileSystemBuilder


class ContainerBuilder(CondaStoreBuilder):
    build_artifact = [
        "DOCKER_BLOB",
        "DOCKER_MANIFEST",
        "CONTAINER_REGISTRY",
    ]

    depends_on = [
        FileSystemBuilder,
    ]

    default_docker_base_image = Union(
        [Unicode(), Callable()],
        help="default base image used for the Dockerized environments. Make sure to have a proper glibc within image (highly discourage alpine/musl based images). Can also be callable function which takes the `orm.Build` object as input which has access to all attributes about the build such as install packages, requested packages, name, namespace, etc",
        config=True,
    )

    @default("default_docker_base_image")
    def _default_docker_base_image(self):
        def _docker_base_image(build: orm.Build):
            return "registry-1.docker.io/library/debian:sid-slim"

        return _docker_base_image

    def _build_conda_docker(self, conda_store, build):
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
        base_image = conda_store.container_registry.pull_image(
            utils.callable_or_value(self.default_docker_base_image, build)
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

        if "DOCKER_MANIFEST" in conda_store.build_artifacts:
            conda_store.container_registry.store_image(conda_store, build, image)

        if "CONTAINER_REGISTRY" in conda_store.build_artifacts:
            conda_store.container_registry.push_image(conda_store, build, image)


    def build_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        build = api.get_build(conda_store.db, build_id)
        if artifact_type == "DOCKER_MANIFEST":
            self._build_conda_docker(conda_store, build)

    def delete_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        if artifact_type == "CONTAINER_REGISTRY":
            self.log.warning("Container registries generally do not support deletion. Deletion is a NO-OP")
        elif artifact_type == "DOCKER_MANIFEST":
            for build_artifact in api.list_build_artifacts(
                db=conda_store.db,
                build_id=build_id,
                included_artifact_types=[artifact_type]
            ):
                conda_store.storage.delete(
                    conda_store.db, build_artifact.build.id, build_artifact.key
                )
        elif artifact_type == "DOCKER_BLOB":
            for build_artifact in api.list_build_artifacts(
                db=conda_store.db,
                build_id=build_id,
                included_artifact_types=[artifact_type]
            ):
                conda_store.storage.delete(
                    conda_store.db, build_artifact.build.id, build_artifact.key
                )
