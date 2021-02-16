import json
import time

from flask import Blueprint, redirect, Response

from conda_store.server.utils import get_conda_store
from conda_store import schema, api


app_registry = Blueprint("registry", __name__)


def _json_response(data, status=200, mimetype="application/json"):
    response = Response(json.dumps(data, indent=3), status=status, mimetype=mimetype)
    response.headers["Docker-Distribution-Api-Version"] = "registry/2.0"
    return response


def docker_error_message(docker_registry_error: schema.DockerRegistryError):
    return _json_response(
        {
            "errors": [
                {
                    "code": docker_registry_error.name,
                    "message": docker_registry_error.value["message"],
                    "detail": docker_registry_error.value["detail"],
                }
            ]
        },
        status=docker_registry_error.value["status"],
    )


def dynamic_conda_store_environment(conda_store, packages):
    def replace_words(s, words):
        for k, v in words.items():
            s = s.replace(k, v)
        return s

    constraint_mapper = {
        ".gt.": ">",
        ".ge.": ">=",
        ".lt.": "<",
        ".le.": "<=",
        ".eq.": "==",
    }

    # TODO: should really be doing checking on package names to
    # validate user input
    packages = [replace_words(_, constraint_mapper) for _ in sorted(packages)]
    environment_name = "|".join(packages)
    environment = api.get_environment(
        conda_store.db, environment_name, namespace="conda-store-dynamic"
    )

    if environment is None:
        environment_specification = {
            "name": environment_name,
            "channels": ["conda-forge"],
            "dependencies": packages,
        }
        conda_store.register_environment(
            environment_specification, namespace="conda-store-dynamic"
        )
    return environment_name


def get_docker_image_manifest(conda_store, image, tag, timeout=10 * 60):
    namespace, *image_name = image.split("/")

    # /v2/<image-name>/manifest/<tag>
    if len(image_name) == 0:
        return docker_error_message(schema.DockerRegistryError.NAME_UNKNOWN)

    if namespace == "conda-store-dynamic":
        environment_name = dynamic_conda_store_environment(conda_store, image_name)
    elif len(image_name) > 1:
        return docker_error_message(schema.DockerRegistryError.NAME_UNKNOWN)
    else:
        environment_name = image_name[0]

    # check that namespace/environment_name exist
    environment = api.get_environment(
        conda_store.db, environment_name, namespace=namespace
    )
    if environment is None:
        return docker_error_message(schema.DockerRegistryError.NAME_UNKNOWN)

    if tag == "latest":
        # waiting for image to be built by conda-store
        start_time = time.time()
        while environment.specification is None:
            conda_store.db.refresh(environment)
            time.sleep(10)
            if time.time() - start_time > timeout:
                return docker_error_message(schema.DockerRegistryError.MANIFEST_UNKNOWN)

        specification_sha256 = environment.specification.sha256
    else:
        specification_sha256 = tag

    manifests_key = f"docker/manifest/{environment_name}/{specification_sha256}"
    return redirect(conda_store.storage.get_url(manifests_key))


def get_docker_image_blob(conda_store, image, blobsum):
    blob_key = f"docker/blobs/{blobsum}"
    return redirect(conda_store.storage.get_url(blob_key))


@app_registry.route("/v2/")
def v2():
    return _json_response({})


@app_registry.route("/v2/<path:rest>")
def list_tags(rest):
    parts = rest.split("/")
    conda_store = get_conda_store()

    # /v2/<image>/tags/list
    if len(parts) > 2 and parts[-2:] == ["tags", "list"]:
        image = "/".join(parts[:-2])
        raise NotImplementedError()
    # /v2/<image>/manifests/<tag>
    elif len(parts) > 2 and parts[-2] == "manifests":
        image = "/".join(parts[:-2])
        tag = parts[-1]
        return get_docker_image_manifest(conda_store, image, tag)
    # /v2/<image>/blobs/<blobsum>
    elif len(parts) > 2 and parts[-2] == "blobs":
        image = "/".join(parts[:-2])
        blobsum = parts[-1].split(":")[1]
        return get_docker_image_blob(conda_store, image, blobsum)
    else:
        return docker_error_message(schema.DockerRegistryError.UNSUPPORTED)
