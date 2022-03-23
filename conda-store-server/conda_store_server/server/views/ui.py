from flask import (
    Blueprint,
    render_template,
    redirect,
    Response,
    url_for,
)
import yaml

from conda_store_server import api
from conda_store_server.server.utils import get_conda_store, get_auth, get_server
from conda_store_server.server.auth import Permissions
from conda_store_server.conda import conda_platform

app_ui = Blueprint("ui", __name__, template_folder="templates")


@app_ui.route("/create/", methods=["GET"])
def ui_create_get_environment():
    conda_store = get_conda_store()
    auth = get_auth()

    orm_namespaces = auth.filter_namespaces(
        api.list_namespaces(conda_store.db, show_soft_deleted=False)
    )

    context = {
        "namespaces": orm_namespaces.all(),
        "entity": auth.authenticate_request(),
    }

    return render_template("create.html", **context)


@app_ui.route("/", methods=["GET"])
def ui_list_environments():
    conda_store = get_conda_store()
    server = get_server()
    auth = get_auth()

    orm_environments = auth.filter_environments(
        api.list_environments(conda_store.db, show_soft_deleted=False)
    )

    context = {
        "environments": orm_environments.all(),
        "registry_external_url": server.registry_external_url,
        "entity": auth.authenticate_request(),
    }

    return render_template("home.html", **context)


@app_ui.route("/namespace/", methods=["GET"])
def ui_list_namespaces():
    conda_store = get_conda_store()
    auth = get_auth()

    orm_namespaces = auth.filter_namespaces(
        api.list_namespaces(conda_store.db, show_soft_deleted=False)
    )

    context = {
        "namespaces": orm_namespaces.all(),
        "entity": auth.authenticate_request(),
    }

    return render_template("namespace.html", **context)


@app_ui.route("/environment/<namespace>/<name>/", methods=["GET"])
def ui_get_environment(namespace, name):
    conda_store = get_conda_store()
    auth = get_auth()

    auth.authorize_request(
        f"{namespace}/{name}", {Permissions.ENVIRONMENT_READ}, require=True
    )

    environment = api.get_environment(conda_store.db, namespace=namespace, name=name)
    if environment is None:
        return (
            render_template(
                "404.html",
                message=f"environment namespace={namespace} name={name} not found",
            ),
            404,
        )

    context = {
        "environment": environment,
        "entity": auth.authenticate_request(),
        "spec": yaml.dump(environment.current_build.specification.spec),
    }

    return render_template("environment.html", **context)


@app_ui.route("/environment/<namespace>/<name>/edit/", methods=["GET"])
def ui_edit_environment(namespace, name):
    conda_store = get_conda_store()

    auth = get_auth()
    auth.authorize_request(
        f"{namespace}/{name}", {Permissions.ENVIRONMENT_CREATE}, require=True
    )

    environment = api.get_environment(conda_store.db, namespace=namespace, name=name)
    if environment is None:
        return (
            render_template(
                "404.html",
                message=f"environment namespace={namespace} name={name} not found",
            ),
            404,
        )

    context = {
        "environment": environment,
        "entity": auth.authenticate_request(),
        "specification": yaml.dump(environment.current_build.specification.spec),
        "namespaces": [environment.namespace],
    }

    return render_template("create.html", **context)


@app_ui.route("/build/<build_id>/", methods=["GET"])
def ui_get_build(build_id):
    conda_store = get_conda_store()
    server = get_server()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return (
            render_template("404.html", message=f"build id={build_id} not found"),
            404,
        )

    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    context = {
        "build": build,
        "registry_external_url": server.registry_external_url,
        "entity": auth.authenticate_request(),
        "platform": conda_platform(),
        "spec": yaml.dump(build.specification.spec),
    }

    return render_template("build.html", **context)


@app_ui.route("/user/", methods=["GET"])
def ui_get_user():
    auth = get_auth()

    entity = auth.authenticate_request()
    if entity is None:
        return redirect(f"{url_for('ui.ui_list_environments')}login/")

    entity_binding_permissions = auth.authorization.get_entity_binding_permissions(
        entity.role_bindings, authenticated=True
    )

    context = {
        "username": entity.primary_namespace,
        "entity_binding_permissions": entity_binding_permissions,
    }
    return render_template("user.html", **context)


@app_ui.route("/build/<build_id>/logs/", methods=["GET"])
def api_get_build_logs(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    return redirect(conda_store.storage.get_url(build.log_key))


@app_ui.route("/build/<build_id>/lockfile/", methods=["GET"])
def api_get_build_lockfile(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    lockfile = api.get_build_lockfile(conda_store.db, build_id)
    return Response(lockfile, mimetype="text/plain")


@app_ui.route("/build/<build_id>/archive/", methods=["GET"])
def api_get_build_archive(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    return redirect(conda_store.storage.get_url(build.conda_pack_key))
