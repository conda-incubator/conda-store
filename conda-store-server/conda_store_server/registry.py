import gzip
import hashlib
import urllib.parse

from conda_store_server import orm, schema, utils
from python_docker.registry import Image, Registry
from sqlalchemy.orm import Session
from traitlets import Callable, Dict, default
from traitlets.config import LoggingConfigurable


class ContainerRegistry(LoggingConfigurable):
    container_registries = Dict(
        {},
        help="Registries url to upload built container images with callable function to configure registry instance with credentials",
        config=True,
    )

    container_registry_image_name = Callable(
        help="Image name to assign to docker image pushed for particular registry",
        config=True,
    )

    @default("container_registry_image_name")
    def _default_container_registry_image_name(self):
        def _container_registry_image_name(registry: Registry, build: orm.Build):
            return f"{registry.username}/{build.environment.namespace.name}-{build.environment.name}"

        return _container_registry_image_name

    container_registry_image_tag = Callable(
        help="Image name and tag to assign to docker image pushed for particular registry",
        config=True,
    )

    @default("container_registry_image_tag")
    def _default_container_registry_image_tag(self):
        def _container_registry_image_tag(registry: Registry, build: orm.Build):
            return build.key

        return _container_registry_image_tag

    def store_image(self, db: Session, conda_store, build: orm.Build, image: Image):
        self.log.info("storing container image locally")
        with utils.timer(self.log, "storing container image locally"):
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
                    db,
                    build.id,
                    build.docker_blob_key(content_compressed_hash),
                    content_compressed,
                    content_type="application/gzip",
                    artifact_type=schema.BuildArtifactType.DOCKER_BLOB,
                )

                docker_layer = schema.DockerManifestLayer(
                    size=len(content_compressed),
                    digest=f"sha256:{content_compressed_hash}",
                )
                docker_manifest.layers.append(docker_layer)

                docker_config_history = schema.DockerConfigHistory()
                docker_config.history.append(docker_config_history)

                docker_config.rootfs.diff_ids.append(
                    f"sha256:{content_uncompressed_hash}"
                )

            docker_config_content = docker_config.json().encode("utf-8")
            docker_config_hash = hashlib.sha256(docker_config_content).hexdigest()
            docker_manifest.config = schema.DockerManifestConfig(
                size=len(docker_config_content), digest=f"sha256:{docker_config_hash}"
            )
            docker_manifest_content = docker_manifest.json().encode("utf-8")
            docker_manifest_hash = hashlib.sha256(docker_manifest_content).hexdigest()

            conda_store.storage.set(
                db,
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
                db,
                build.id,
                f"docker/manifest/sha256:{docker_manifest_hash}",
                docker_manifest_content,
                content_type="application/vnd.docker.distribution.manifest.v2+json",
                artifact_type=schema.BuildArtifactType.DOCKER_BLOB,
            )

            conda_store.storage.set(
                db,
                build.id,
                build.docker_manifest_key,
                docker_manifest_content,
                content_type="application/vnd.docker.distribution.manifest.v2+json",
                artifact_type=schema.BuildArtifactType.DOCKER_MANIFEST,
            )

            conda_store.log.info(
                f"built docker image: {image.name}:{image.tag} layers={len(image.layers)}"
            )

    @staticmethod
    def parse_image_uri(image_name: str):
        """Must be in fully specified format [<scheme>://]<registry_url>/<image_name>:<tag_name>"""
        if not image_name.startswith("http"):
            image_name = f"https://{image_name}"

        parsed_url = urllib.parse.urlparse(image_name)
        registry_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        image_name, tag_name = parsed_url.path.split(":", 1)
        image_name = image_name[1:]  # remove beginning "/"
        return registry_url, image_name, tag_name

    def pull_image(self, image_name: str) -> Image:
        """Must be in fully specified format [<scheme>://]<registry_url>/<image_name>:<tag_name>

        Docker is the only weird registry where you must use:
          - `https://registry-1.docker.io`
        """
        registry_url, name, tag = self.parse_image_uri(image_name)

        for url in self.container_registries:
            if registry_url in url:
                registry = self.container_registries[registry_url](url)
                break
        else:
            self.log.warning(
                f"registry {registry_url} not configured using registry without authentication"
            )
            registry = Registry(hostname=registry_url)

        return registry.pull_image(name, tag)

    def push_image(self, db, build, image: Image):
        for registry_url, configure_registry in self.container_registries.items():
            self.log.info(f"beginning upload of image to registry {registry_url}")
            with utils.timer(self.log, f"uploading image to registry {registry_url}"):
                registry = configure_registry(registry_url)
                image.name = self.container_registry_image_name(registry, build)
                image.tag = self.container_registry_image_tag(registry, build)
                registry.push_image(image)

                registry_build_artifact = orm.BuildArtifact(
                    build_id=build.id,
                    artifact_type=schema.BuildArtifactType.CONTAINER_REGISTRY,
                    key=f"{registry_url}/{image.name}:{image.tag}",
                )
                db.add(registry_build_artifact)
                db.commit()

    def delete_image(self, image_name: str):
        registry_url, name, tag = self.parse_image_uri(image_name)

        for url in self.container_registries:
            if registry_url in url:
                registry = self.container_registries[registry_url](url)
                break
        else:
            self.log.warning(
                f"registry {registry_url} not configured using registry without authentication"
            )
            registry = Registry(hostname=registry_url)

        self.log.info(f"deleting container image {image_name}")
        registry.delete_image(name, tag)
