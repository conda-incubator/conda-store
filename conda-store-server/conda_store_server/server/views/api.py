from flask import Blueprint, jsonify, redirect, request
import pydantic

from conda_store_server import api, schema
from conda_store_server.server.utils import get_conda_store

app_api = Blueprint("api", __name__)


@app_api.route("/api/v1/")
def api_status():
    return jsonify({"status": "ok"})


@app_api.route("/api/v1/environment/")
def api_list_environments():
    conda_store = get_conda_store()
    orm_environments = api.list_environments(conda_store.db)
    environments = [
        schema.Environment.from_orm(_).dict(exclude={"specification": {"builds"}})
        for _ in orm_environments
    ]
    return jsonify(environments)


@app_api.route("/api/v1/environment/<name>/", methods=["GET"])
def api_get_environment(name):
    conda_store = get_conda_store()
    environment = schema.Environment.from_orm(
        api.get_environment(conda_store.db, name)
    ).dict()
    return jsonify(environment)


@app_api.route("/api/v1/specification/", methods=["GET"])
def api_list_specification():
    conda_store = get_conda_store()
    orm_specifications = api.list_specifications(conda_store.db)
    specifications = [
        schema.Specification.from_orm(_).dict(exclude={"builds"})
        for _ in orm_specifications
    ]
    return jsonify(specifications)


@app_api.route("/api/v1/specification/", methods=["POST"])
def api_post_specification():
    conda_store = get_conda_store()
    try:
        specification = schema.CondaSpecification.parse_obj(request.json)
        api.post_specification(conda_store, specification)
        return jsonify({"status": "ok"})
    except pydantic.ValidationError as e:
        return jsonify({"status": "error", "error": e.errors()}), 400


@app_api.route("/api/v1/specification/<sha256>/", methods=["GET"])
def api_get_specification(sha256):
    conda_store = get_conda_store()
    specification = schema.Specification.from_orm(
        api.get_specification(conda_store.db, sha256)
    )
    return jsonify(specification.dict(exclude={"builds"}))


@app_api.route("/api/v1/build/", methods=["GET"])
def api_list_builds():
    conda_store = get_conda_store()
    orm_builds = api.list_builds(conda_store.db)
    builds = [
        schema.Build.from_orm(build).dict(exclude={"packages"}) for build in orm_builds
    ]
    return jsonify(builds)


@app_api.route("/api/v1/build/<build_id>/", methods=["GET"])
def api_get_build(build_id):
    conda_store = get_conda_store()
    build = schema.Build.from_orm(api.get_build(conda_store.db, build_id))
    return jsonify(build.dict())


@app_api.route("/api/v1/build/<build_id>/logs/", methods=["GET"])
def api_get_build_logs(build_id):
    conda_store = get_conda_store()
    log_key = api.get_build(conda_store.db, build_id).log_key
    return redirect(conda_store.storage.get_url(log_key))


@app_api.route("/api/v1/package/<provider>/", methods=["GET"])
def api_list_packages(provider):
    conda_store = get_conda_store()
    if provider == "conda":
        orm_packages = api.list_conda_packages(conda_store.db)
        packages = [
            schema.CondaPackage.from_orm(package).dict() for package in orm_packages
        ]
        return jsonify(packages)
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f'package provider "{provider}" not supported',
                }
            ),
            400,
        )
