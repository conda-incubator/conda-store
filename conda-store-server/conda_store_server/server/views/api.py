from flask import Blueprint, jsonify, redirect, request
import pydantic
from typing import List, Dict

import yaml

from conda_store_server import api, orm, schema, utils
from conda_store_server.server.utils import get_conda_store, get_auth, get_server
from conda_store_server.server.auth import Permissions


app_api = Blueprint("api", __name__)


def filter_distinct_on(
    query, allowed_distinct_ons: Dict = {}, default_distinct_on: List = []
):
    distinct_on = request.args.getlist("distinct_on") or default_distinct_on
    distinct_on = [
        allowed_distinct_ons[d] for d in distinct_on if d in allowed_distinct_ons
    ]

    if distinct_on:
        return distinct_on, query.distinct(*distinct_on)
    return distinct_on, query


def get_limit_offset_args(request):
    server = get_server()

    page = int(request.args.get("page", 1))
    size = min(
        int(request.args.get("size", server.max_page_size)), server.max_page_size
    )
    offset = (page - 1) * size
    return size, offset


def get_sorts(
    request,
    allowed_sort_bys: Dict = {},
    required_sort_bys: List = [],
    default_sort_by: List = [],
    default_order: str = "asc",
):
    sort_by = request.args.getlist("sort_by") or default_sort_by
    sort_by = [allowed_sort_bys[s] for s in sort_by if s in allowed_sort_bys]

    # required_sort_bys is needed when sorting is used with distinct
    # query see "SELECT DISTINCT ON expressions must match initial
    # ORDER BY expressions"
    if required_sort_bys != sort_by[: len(required_sort_bys)]:
        sort_by = required_sort_bys + sort_by

    order = request.args.get("order", default_order)
    if order not in {"asc", "desc"}:
        order = default_order

    order_mapping = {"asc": lambda c: c.asc(), "desc": lambda c: c.desc()}
    return [order_mapping[order](k) for k in sort_by]


def paginated_api_response(
    query,
    object_schema,
    sorts: List = [],
    exclude=None,
    allowed_sort_bys: Dict = {},
    required_sort_bys: List = [],
    default_sort_by: List = [],
    default_order: str = "asc",
):

    limit, offset = get_limit_offset_args(request)
    sorts = get_sorts(
        request,
        allowed_sort_bys,
        required_sort_bys=required_sort_bys,
        default_sort_by=default_sort_by,
        default_order=default_order,
    )

    count = query.count()
    query = query.order_by(*sorts).limit(limit).offset(offset)

    return jsonify(
        {
            "status": "ok",
            "data": [
                object_schema.from_orm(_).dict(exclude=exclude) for _ in query.all()
            ],
            "page": (offset // limit) + 1,
            "size": limit,
            "count": count,
        }
    )


@app_api.route("/api/v1/")
def api_status():
    return jsonify({"status": "ok"})


@app_api.route("/api/v1/permission/")
def api_get_permissions():
    conda_store = get_conda_store()
    auth = get_auth()

    entity = auth.authenticate_request(require=False)
    authenticated = entity is not None

    entity_binding_permissions = auth.authorization.get_entity_binding_permissions(
        entity.role_bindings if authenticated else {}, authenticated=authenticated
    )

    # convert Dict[str, set[enum]] -> Dict[str, List[str]]
    # to be json serializable
    entity_binding_permissions = {
        entity_arn: [_.value for _ in entity_permissions]
        for entity_arn, entity_permissions in entity_binding_permissions.items()
    }

    return jsonify(
        {
            "status": "ok",
            "data": {
                "authenticated": authenticated,
                "entity_permissions": entity_binding_permissions,
                "primary_namespace": entity.primary_namespace
                if authenticated
                else conda_store.default_namespace,
            },
        }
    )


@app_api.route("/api/v1/namespace/")
def api_list_namespaces():
    conda_store = get_conda_store()
    auth = get_auth()

    orm_namespaces = auth.filter_namespaces(
        api.list_namespaces(conda_store.db, show_soft_deleted=False)
    )
    return paginated_api_response(
        orm_namespaces,
        schema.Namespace,
        allowed_sort_bys={
            "name": orm.Namespace.name,
        },
        default_sort_by=["name"],
    )


@app_api.route("/api/v1/namespace/<namespace>/")
def api_get_namespace(namespace):
    conda_store = get_conda_store()
    auth = get_auth()

    auth.authorize_request(namespace, {Permissions.NAMESPACE_READ}, require=True)

    namespace = api.get_namespace(conda_store.db, namespace)
    if namespace is None:
        return jsonify({"status": "error", "message": "namespace does not exist"}), 404

    return jsonify(
        {
            "status": "ok",
            "data": schema.Namespace.from_orm(namespace).dict(),
        }
    )


@app_api.route("/api/v1/namespace/<namespace>/", methods=["POST"])
def api_create_namespace(namespace):
    conda_store = get_conda_store()
    auth = get_auth()

    auth.authorize_request(namespace, {Permissions.NAMESPACE_CREATE}, require=True)

    namespace_orm = api.get_namespace(conda_store.db, namespace)
    if namespace_orm:
        return jsonify({"status": "error", "message": "namespace already exists"}), 409

    try:
        api.create_namespace(conda_store.db, namespace)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e.args[0])}), 400
    conda_store.db.commit()
    return jsonify({"status": "ok"})


@app_api.route("/api/v1/namespace/<namespace>/", methods=["DELETE"])
def api_delete_namespace(namespace):
    conda_store = get_conda_store()
    auth = get_auth()

    auth.authorize_request(namespace, {Permissions.NAMESPACE_DELETE}, require=True)

    namespace_orm = api.get_namespace(conda_store.db, namespace)
    if namespace_orm is None:
        return jsonify({"status": "error", "message": "namespace does not exist"}), 404

    conda_store.delete_namespace(namespace)
    return jsonify({"status": "ok"})


@app_api.route("/api/v1/environment/")
def api_list_environments():
    conda_store = get_conda_store()
    auth = get_auth()

    search = request.args.get("search")

    orm_environments = auth.filter_environments(
        api.list_environments(conda_store.db, search=search, show_soft_deleted=False)
    )
    return paginated_api_response(
        orm_environments,
        schema.Environment,
        exclude={"current_build"},
        allowed_sort_bys={
            "namespace": orm.Namespace.name,
            "name": orm.Environment.name,
        },
        default_sort_by=["namespace", "name"],
    )


@app_api.route("/api/v1/environment/<namespace>/<name>/", methods=["GET"])
def api_get_environment(namespace, name):
    conda_store = get_conda_store()
    auth = get_auth()

    auth.authorize_request(
        f"{namespace}/{name}", {Permissions.ENVIRONMENT_READ}, require=True
    )

    environment = api.get_environment(conda_store.db, namespace=namespace, name=name)
    if environment is None:
        return (
            jsonify({"status": "error", "message": "environment does not exist"}),
            404,
        )

    return jsonify(
        {
            "status": "ok",
            "data": schema.Environment.from_orm(environment).dict(
                exclude={"current_build"}
            ),
        }
    )


@app_api.route("/api/v1/environment/<namespace>/<name>/", methods=["PUT"])
def api_update_environment_build(namespace, name):
    conda_store = get_conda_store()
    auth = get_auth()

    auth.authorize_request(
        f"{namespace}/{name}", {Permissions.ENVIRONMENT_UPDATE}, require=True
    )

    data = request.json
    if "build_id" not in data:
        return jsonify({"status": "error", "message": "build id not specificated"}), 400

    try:
        build_id = data["build_id"]
        conda_store.update_environment_build(namespace, name, build_id)
    except utils.CondaStoreError as e:
        return e.response

    return jsonify({"status": "ok"})


@app_api.route("/api/v1/environment/<namespace>/<name>/", methods=["DELETE"])
def api_delete_environment(namespace, name):
    conda_store = get_conda_store()
    auth = get_auth()

    auth.authorize_request(
        f"{namespace}/{name}", {Permissions.ENVIRONMENT_DELETE}, require=True
    )

    conda_store.delete_environment(namespace, name)
    return jsonify({"status": "ok"})


@app_api.route("/api/v1/specification/", methods=["POST"])
def api_post_specification():
    conda_store = get_conda_store()
    auth = get_auth()

    permissions = {Permissions.ENVIRONMENT_CREATE}

    namespace_name = request.json.get("namespace") or conda_store.default_namespace
    namespace = api.get_namespace(conda_store.db, namespace_name)
    if namespace is None:
        permissions.add(Permissions.NAMESPACE_CREATE)

    try:
        specification = request.json.get("specification")
        specification = yaml.safe_load(specification)
        specification = schema.CondaSpecification.parse_obj(specification)
    except yaml.error.YAMLError:
        return (
            jsonify({"status": "error", "message": "Unable to parse. Invalid YAML"}),
            400,
        )
    except pydantic.ValidationError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    auth.authorize_request(
        f"{namespace_name}/{specification.name}",
        permissions,
        require=True,
    )

    try:
        build_id = api.post_specification(conda_store, specification, namespace_name)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e.args[0])}), 400

    return jsonify({"status": "ok", "data": {"build_id": build_id}})


@app_api.route("/api/v1/build/", methods=["GET"])
def api_list_builds():
    conda_store = get_conda_store()
    auth = get_auth()

    orm_builds = auth.filter_builds(
        api.list_builds(conda_store.db, show_soft_deleted=True)
    )
    return paginated_api_response(
        orm_builds,
        schema.Build,
        exclude={"specification", "packages"},
        allowed_sort_bys={
            "id": orm.Build.id,
        },
        default_sort_by=["id"],
    )


@app_api.route("/api/v1/build/<build_id>/", methods=["GET"])
def api_get_build(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return jsonify({"status": "error", "message": "build id does not exist"}), 404

    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    return jsonify(
        {
            "status": "ok",
            "data": schema.Build.from_orm(build).dict(exclude={"packages"}),
        }
    )


@app_api.route("/api/v1/build/<build_id>/", methods=["PUT"])
def api_put_build(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return jsonify({"status": "error", "message": "build id does not exist"}), 404

    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_UPDATE},
        require=True,
    )

    conda_store.create_build(build.environment_id, build.specification.sha256)
    return jsonify({"status": "ok", "message": "rebuild triggered"})


@app_api.route("/api/v1/build/<build_id>/", methods=["DELETE"])
def api_delete_build(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return jsonify({"status": "error", "message": "build id does not exist"}), 404

    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.BUILD_DELETE},
        require=True,
    )

    conda_store.delete_build(build_id)
    return jsonify({"status": "ok"})


@app_api.route("/api/v1/build/<build_id>/packages/", methods=["GET"])
def api_get_build_packages(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return jsonify({"status": "error", "message": "build id does not exist"}), 404

    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    search = request.args.get("search")
    exact = request.args.get("exact")

    build_str = request.args.get("build")
    orm_packages = api.get_build_packages(
        conda_store.db, build.id, search=search, exact=exact, build=build_str
    )
    return paginated_api_response(
        orm_packages,
        schema.CondaPackage,
        allowed_sort_bys={
            "channel": orm.CondaChannel.name,
            "name": orm.CondaPackage.name,
        },
        default_sort_by=["channel", "name"],
        exclude={"channel": {"last_update"}},
    )


@app_api.route("/api/v1/build/<build_id>/logs/", methods=["GET"])
def api_get_build_logs(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return jsonify({"status": "error", "message": "build id does not exist"}), 404

    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    return redirect(conda_store.storage.get_url(build.log_key))


@app_api.route("/api/v1/channel/", methods=["GET"])
def api_list_channels():
    conda_store = get_conda_store()

    orm_channels = api.list_conda_channels(conda_store.db)
    return paginated_api_response(
        orm_channels,
        schema.CondaChannel,
        allowed_sort_bys={"name": orm.CondaChannel.name},
        default_sort_by=["name"],
    )


@app_api.route("/api/v1/package/", methods=["GET"])
def api_list_packages():
    conda_store = get_conda_store()

    search = request.args.get("search")
    exact = request.args.get("exact")

    build = request.args.get("build")

    orm_packages = api.list_conda_packages(
        conda_store.db, search=search, exact=exact, build=build
    )
    required_sort_bys, distinct_orm_packages = filter_distinct_on(
        orm_packages,
        allowed_distinct_ons={
            "channel": orm.CondaChannel.name,
            "name": orm.CondaPackage.name,
            "version": orm.CondaPackage.version,
        },
    )
    return paginated_api_response(
        distinct_orm_packages,
        schema.CondaPackage,
        allowed_sort_bys={
            "channel": orm.CondaChannel.name,
            "name": orm.CondaPackage.name,
            "version": orm.CondaPackage.version,
            "build": orm.CondaPackage.build,
        },
        default_sort_by=["channel", "name", "version", "build"],
        required_sort_bys=required_sort_bys,
        exclude={"channel": {"last_update"}},
    )


@app_api.route("/api/v1/build/<build_id>/yaml/", methods=["GET"])
def api_get_build_yaml(build_id):
    conda_store = get_conda_store()
    auth = get_auth()

    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return jsonify({"status": "error", "message": "build id does not exist"}), 404

    auth.authorize_request(
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )
    return redirect(conda_store.storage.get_url(build.conda_env_export_key))
