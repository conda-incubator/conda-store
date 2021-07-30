from flask import Blueprint, render_template, request, redirect, Response, g, abort, jsonify
import pydantic
import yaml

from conda_store_server import api, schema
from conda_store_server.server.utils import get_conda_store, get_auth
from conda_store_server.server.auth import Permissions
from conda_store_server.conda import conda_platform

app_ui = Blueprint("ui", __name__, template_folder="templates")


@app_ui.route("/create/", methods=["GET", "POST"])
def ui_create_get_environment():
    conda_store = get_conda_store()
    auth = get_auth()

    orm_namespaces = auth.filter_namespaces(
        api.list_namespaces(conda_store.db))

    if request.method == "GET":
        return render_template(
            "create.html",
            namespaces=orm_namespaces.all(),
        )
    elif request.method == "POST":
        try:
            namespace_id = int(request.form.get("namespace"))
            specification_text = request.form.get("specification")
            specification = schema.CondaSpecification.parse_obj(
                yaml.safe_load(specification_text)
            )
            namespace = api.get_namespace(conda_store.db, id=namespace_id)
            api.post_specification(conda_store, specification.dict(), namespace.name)
            return redirect("/")
        except yaml.YAMLError:
            return render_template(
                "create.html",
                specification=specification_text,
                message="Unable to parse. Invalid YAML",
                namespaces=orm_namespaces.all(),
            )
        except pydantic.ValidationError as e:
            return render_template(
                "create.html",
                specification=specification_text,
                message=str(e),
                namespaces=orm_namespaces.all(),
            )


@app_ui.route("/", methods=["GET"])
def ui_list_environments():
    conda_store = get_conda_store()
    auth = get_auth()

    orm_environments = auth.filter_environments(
        api.list_environments(conda_store.db))

    return render_template(
        "home.html",
        environments=orm_environments.all(),
    )


@app_ui.route("/environment/<namespace>/<name>/", methods=["GET"])
def ui_get_environment(namespace, name):
    conda_store = get_conda_store()
    auth = get_auth()

    auth.authorize_request(
        f'{namespace}/{name}',
        {Permissions.ENVIRONMENT_READ},
        require=True)

    return render_template(
        "environment.html",
        environment=api.get_environment(conda_store.db, namespace=namespace, name=name),
        environment_builds=api.get_environment_builds(conda_store.db, namespace, name),
    )


@app_ui.route("/environment/<namespace>/<name>/edit/", methods=["GET"])
def ui_edit_environment(namespace, name):
    conda_store = get_conda_store()

    auth = get_auth()
    auth.authorize_request(
        f'{namespace}/{name}', {Permissions.ENVIRONMENT_CREATE}, require=True)

    environment = api.get_environment(conda_store.db, namespace=namespace, name=name)
    specification = api.get_specification(
        conda_store.db,
        environment.specification.sha256,
    )
    namespace = api.get_namespace(conda_store.db, namespace)
    return render_template(
        "create.html",
        specification=yaml.dump(specification.spec),
        namespaces=[namespace],
    )


@app_ui.route("/specification/<sha256>/", methods=["GET"])
def ui_get_specification(sha256):
    conda_store = get_conda_store()
    specification = api.get_specification(conda_store.db, sha256)
    return render_template(
        "specification.html",
        specification=specification,
        spec=yaml.dump(specification.spec),
    )


@app_ui.route("/build/<build_id>/", methods=["GET"])
def ui_get_build(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return render_template("404.html", message=f"build {build_id} not found"), 404

    auth.authorize_request(
        f'{build.namespace.name}/{build.specification.name}',
        {Permissions.ENVIRONMENT_READ},
        require=True)

    return render_template("build.html", build=build, platform=conda_platform())


@app_ui.route("/build/<build_id>/logs/", methods=["GET"])
def api_get_build_logs(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    auth.authorize_request(
        f'{build.namespace.name}/{build.specification.name}',
        {Permissions.ENVIRONMENT_READ},
        require=True)

    return redirect(conda_store.storage.get_url(build.log_key))


@app_ui.route("/build/<build_id>/lockfile/", methods=["GET"])
def api_get_build_lockfile(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    auth.authorize_request(
        f'{build.namespace.name}/{build.specification.name}',
        {Permissions.ENVIRONMENT_READ},
        require=True)

    lockfile = api.get_build_lockfile(conda_store.db, build_id)
    return Response(lockfile, mimetype="text/plain")


@app_ui.route("/build/<build_id>/yaml/", methods=["GET"])
def api_get_build_yaml(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    auth.authorize_request(
        f'{build.namespace.name}/{build.specification.name}',
        {Permissions.ENVIRONMENT_READ},
        require=True)

    return redirect(conda_store.storage.get_url(build.conda_env_export_key))


@app_ui.route("/build/<build_id>/archive/", methods=["GET"])
def api_get_build_archive(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    auth.authorize_request(
        f'{build.namespace.name}/{build.specification.name}',
        {Permissions.ENVIRONMENT_READ},
        require=True)

    return redirect(conda_store.storage.get_url(build.conda_pack_key))
