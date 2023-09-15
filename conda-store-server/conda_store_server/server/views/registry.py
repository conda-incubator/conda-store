import json
import time

from conda_store_server import api, orm, schema
from conda_store_server.schema import Permissions
from conda_store_server.server import dependencies
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response

router_registry = APIRouter(tags=["registry"])


def _json_response(data, status=200, mimetype="application/json"):
    response = Response(
        content=json.dumps(data, indent=3), status_code=status, media_type=mimetype
    )
    response.headers["Docker-Distribution-Api-Version"] = "registry/2.0"
    return response


def docker_error_message(docker_registry_error: schema.DockerRegistryError):
    response = _json_response(
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

    if docker_registry_error == schema.DockerRegistryError.UNAUTHORIZED:
        response.headers["Www-Authenticate"] = 'Basic realm="Registry Realm"'
    return response


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
    package_specs = [replace_words(_, constraint_mapper) for _ in sorted(packages)]
    environment_name = "-".join(packages)
    environment = api.get_environment(
        conda_store.db, environment_name, namespace="conda-store-dynamic"
    )

    if environment is None:
        environment_specification = {
            "name": environment_name,
            "channels": ["conda-forge"],
            "dependencies": package_specs,
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
        conda_store.db, namespace=namespace, name=environment_name
    )
    if environment is None:
        return docker_error_message(schema.DockerRegistryError.NAME_UNKNOWN)

    if tag == "latest":
        build_key = environment.current_build.build_key
    elif tag.startswith("sha256:"):
        # looking for sha256 of docker manifest
        manifests_key = f"docker/manifest/{tag}"
        return RedirectResponse(conda_store.storage.get_url(manifests_key))
    else:
        build_key = tag

    build_id = orm.Build.parse_build_key(build_key)
    if build_id is None:
        return docker_error_message(schema.DockerRegistryError.MANIFEST_UNKNOWN)

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return docker_error_message(schema.DockerRegistryError.MANIFEST_UNKNOWN)

    # waiting for image to be built by conda-store
    start_time = time.time()
    while not build.has_docker_manifest:
        conda_store.db.refresh(build)
        time.sleep(10)
        if time.time() - start_time > timeout:
            return docker_error_message(schema.DockerRegistryError.MANIFEST_UNKNOWN)

    manifests_key = f"docker/manifest/{build_key}"
    return RedirectResponse(conda_store.storage.get_url(manifests_key))


def get_docker_image_blob(conda_store, image, blobsum):
    blob_key = f"docker/blobs/{blobsum}"
    return RedirectResponse(conda_store.storage.get_url(blob_key))


@router_registry.get("/v2/")
def v2(
    request: Request,
    entity=Depends(dependencies.get_entity),
):
    if entity is None:
        return docker_error_message(schema.DockerRegistryError.UNAUTHORIZED)

    return _json_response({})


@router_registry.get(
    "/v2/{rest:path}",
)
def list_tags(
    rest: str,
    request: Request,
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    parts = rest.split("/")
    if len(parts) <= 3:
        return docker_error_message(schema.DockerRegistryError.UNSUPPORTED)

    if entity is None:
        return docker_error_message(schema.DockerRegistryError.UNAUTHORIZED)

    image = "/".join(parts[:-2])

    try:
        auth.authorize_request(
            request,
            image
            if parts[0] != "conda-store-dynamic"
            else "conda-store-dynamic/python",
            {Permissions.ENVIRONMENT_READ},
            require=True,
        )
    except HTTPException as e:
        if e.status_code == 403:
            return docker_error_message(schema.DockerRegistryError.DENIED)

    # /v2/<image>/tags/list
    if parts[-2:] == ["tags", "list"]:
        raise NotImplementedError()
    # /v2/<image>/manifests/<tag>
    elif parts[-2] == "manifests":
        tag = parts[-1]
        return get_docker_image_manifest(conda_store, image, tag)
    # /v2/<image>/blobs/<blobsum>
    elif parts[-2] == "blobs":
        blobsum = parts[-1].split(":")[1]
        return get_docker_image_blob(conda_store, image, blobsum)
