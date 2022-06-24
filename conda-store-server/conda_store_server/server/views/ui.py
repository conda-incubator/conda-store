from typing import Optional

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
import yaml

from conda_store_server import api
from conda_store_server.server import dependencies
from conda_store_server.schema import Permissions
from conda_store_server.conda import conda_platform

router_ui = APIRouter(tags=["ui"])


@router_ui.get("/create/")
def ui_create_get_environment(
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    orm_namespaces = auth.filter_namespaces(
        entity, api.list_namespaces(conda_store.db, show_soft_deleted=False)
    )

    default_namespace = (
        entity.primary_namespace if entity else conda_store.default_namespace
    )

    def sort_namespace(n):
        "Default namespace always first, then alphabetical"
        if n.name == default_namespace:
            return f"0{n.name}"
        return f"1{n.name}"

    context = {
        "request": request,
        "namespaces": sorted(orm_namespaces.all(), key=sort_namespace),
        "entity": entity,
    }

    return templates.TemplateResponse("create.html", context)


@router_ui.get("/")
def ui_list_environments(
    request: Request,
    search: Optional[str] = None,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    server=Depends(dependencies.get_server),
    entity=Depends(dependencies.get_entity),
):
    orm_environments = auth.filter_environments(
        entity,
        api.list_environments(conda_store.db, search=search, show_soft_deleted=False),
    )

    context = {
        "request": request,
        "environments": orm_environments.all(),
        "registry_external_url": server.registry_external_url,
        "entity": entity,
    }

    return templates.TemplateResponse("home.html", context)


@router_ui.get("/namespace/")
def ui_list_namespaces(
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    orm_namespaces = auth.filter_namespaces(
        entity, api.list_namespaces(conda_store.db, show_soft_deleted=False)
    )

    context = {
        "request": request,
        "namespaces": orm_namespaces.all(),
        "entity": entity,
    }

    return templates.TemplateResponse("namespace.html", context)


@router_ui.get("/environment/{namespace}/{environment_name}/")
def ui_get_environment(
    namespace: str,
    environment_name: str,
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    auth.authorize_request(
        request,
        f"{namespace}/{environment_name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    environment = api.get_environment(
        conda_store.db, namespace=namespace, name=environment_name
    )
    if environment is None:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "message": f"environment namespace={namespace} name={environment_name} not found",
            },
            status_code=404,
        )

    context = {
        "request": request,
        "environment": environment,
        "entity": entity,
        "spec": yaml.dump(environment.current_build.specification.spec),
    }

    return templates.TemplateResponse("environment.html", context)


@router_ui.get("/environment/{namespace}/{environment_name}/edit/")
def ui_edit_environment(
    namespace: str,
    environment_name: str,
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    auth.authorize_request(
        request,
        f"{namespace}/{environment_name}",
        {Permissions.ENVIRONMENT_CREATE},
        require=True,
    )

    environment = api.get_environment(
        conda_store.db, namespace=namespace, name=environment_name
    )
    if environment is None:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "message": f"environment namespace={namespace} name={environment_name} not found",
            },
            status_code=404,
        )

    context = {
        "request": request,
        "environment": environment,
        "entity": entity,
        "specification": yaml.dump(environment.current_build.specification.spec),
        "namespaces": [environment.namespace],
    }

    return templates.TemplateResponse("create.html", context)


@router_ui.get("/build/{build_id}/")
def ui_get_build(
    build_id: int,
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    server=Depends(dependencies.get_server),
    entity=Depends(dependencies.get_entity),
):
    build = api.get_build(conda_store.db, build_id)
    if build is None:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "message": f"build id={build_id} not found",
            },
            status_code=404,
        )

    auth.authorize_request(
        request,
        f"{build.environment.namespace.name}/{build.environment.name}",
        {Permissions.ENVIRONMENT_READ},
        require=True,
    )

    context = {
        "request": request,
        "build": build,
        "registry_external_url": server.registry_external_url,
        "entity": entity,
        "platform": conda_platform(),
        "spec": yaml.dump(build.specification.spec),
    }

    return templates.TemplateResponse("build.html", context)


@router_ui.get("/user/")
def ui_get_user(
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    if entity is None:
        return RedirectResponse(f"{request.url_for('ui_list_environments')}login/")

    entity_binding_permissions = auth.authorization.get_entity_binding_permissions(
        entity.role_bindings, authenticated=True
    )

    context = {
        "request": request,
        "username": entity.primary_namespace,
        "entity_binding_permissions": entity_binding_permissions,
    }
    return templates.TemplateResponse("user.html", context)
