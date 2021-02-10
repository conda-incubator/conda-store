import json

from flask import Blueprint, redirect, Response

from conda_store.server.utils import get_conda_store


app_registry = Blueprint("registry", __name__)


def _json_response(data, status=200, mimetype="application/json"):
    response = Response(json.dumps(data, indent=3), status=status, mimetype=mimetype)
    response.headers["Docker-Distribution-Api-Version"] = "registry/2.0"
    return response


@app_registry.route("/v2/")
def v2():
    return _json_response({})


@app_registry.route("/v2/<path:rest>")
def list_tags(rest):
    parts = rest.split("/")
    conda_store = get_conda_store()

    if len(parts) > 2 and parts[-2:] == ["tags", "list"]:
        image = "/".join(parts[:-2])
        raise NotImplementedError()
    elif len(parts) > 2 and parts[-2] == "manifests":
        image = "/".join(parts[:-2])
        tag = parts[-1]
        manifests_key = f"docker/manifest/{image}/{tag}"
        return redirect(conda_store.storage.get_url(manifests_key))
    elif len(parts) > 2 and parts[-2] == "blobs":
        image = "/".join(parts[:-2])
        # example
        # /v2/data-science/blobs/sha256:3d551ef9533252d3e70a3ee55587c03581516d550af921342517e001cafbcced
        blob = parts[-1].split(":")[1]
        blob_key = f"docker/blobs/{blob}"
        return redirect(conda_store.storage.get_url(blob_key))
    else:
        return _json_response({"status": "error", "path": rest}, status=404)
