# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from typing import Optional

import yaml
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from conda_store_server import api
from conda_store_server._internal.action.generate_constructor_installer import (
    get_installer_platform,
)
from conda_store_server._internal.server import dependencies
from conda_store_server.server.schema import Permissions

router_ui = APIRouter(tags=["ui"])


@router_ui.get("/create/")
async def ui_create_get_environment(
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    with conda_store.get_db() as db:
        orm_namespaces = auth.filter_namespaces(
            entity, api.list_namespaces(db, show_soft_deleted=False)
        )

        default_namespace = (
            entity.primary_namespace if entity else conda_store.config.default_namespace
        )

        def sort_namespace(n):
            """Default namespace always first, then alphabetical"""
            if n.name == default_namespace:
                return f"0{n.name}"
            return f"1{n.name}"

        context = {
            "request": request,
            "namespaces": sorted(orm_namespaces.all(), key=sort_namespace),
            "entity": entity,
        }

        return templates.TemplateResponse(request, "create.html", context)


@router_ui.get("/")
async def ui_list_environments(
    request: Request,
    search: Optional[str] = None,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    server=Depends(dependencies.get_server),
    entity=Depends(dependencies.get_entity),
):
    with conda_store.get_db() as db:
        orm_environments = auth.filter_environments(
            entity,
            api.list_environments(db, search=search, show_soft_deleted=False),
        )

        context = {
            "request": request,
            "environments": orm_environments.all(),
            "registry_external_url": server.registry_external_url,
            "entity": entity,
            "platform": get_installer_platform(),
        }

        return templates.TemplateResponse(request, "home.html", context)


@router_ui.get("/namespace/")
async def ui_list_namespaces(
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    with conda_store.get_db() as db:
        orm_namespaces = auth.filter_namespaces(
            entity, api.list_namespaces(db, show_soft_deleted=False)
        )

        context = {
            "request": request,
            "namespaces": orm_namespaces.all(),
            "entity": entity,
        }

        return templates.TemplateResponse(request, "namespace.html", context)


@router_ui.get("/environment/{namespace}/{environment_name}/")
async def ui_get_environment(
    namespace: str,
    environment_name: str,
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    with conda_store.get_db() as db:
        auth.authorize_request(
            request,
            f"{namespace}/{environment_name}",
            {Permissions.ENVIRONMENT_READ},
            require=True,
        )

        environment = api.get_environment(
            db, namespace=namespace, name=environment_name
        )
        if environment is None:
            return templates.TemplateResponse(
                request,
                "404.html",
                {
                    "request": request,
                    "message": f"environment namespace={namespace} name={environment_name} not found",
                },
                status_code=404,
            )

        specification = environment.current_build.specification
        is_lockfile = specification.is_lockfile
        spec = specification.spec
        description = spec["description"]
        if is_lockfile:
            spec = spec["lockfile"]

        context = {
            "request": request,
            "environment": environment,
            "entity": entity,
            "environment_description": description,
            "spec": yaml.dump(spec),
        }

        return templates.TemplateResponse(request, "environment.html", context)


@router_ui.get("/environment/{namespace}/{environment_name}/edit/")
async def ui_edit_environment(
    namespace: str,
    environment_name: str,
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    with conda_store.get_db() as db:
        auth.authorize_request(
            request,
            f"{namespace}/{environment_name}",
            {Permissions.ENVIRONMENT_CREATE},
            require=True,
        )

        environment = api.get_environment(
            db, namespace=namespace, name=environment_name
        )
        if environment is None:
            return templates.TemplateResponse(
                request,
                "404.html",
                {
                    "request": request,
                    "message": f"environment namespace={namespace} name={environment_name} not found",
                },
                status_code=404,
            )

        specification = environment.current_build.specification
        is_lockfile = specification.is_lockfile
        spec = specification.spec
        name = spec["name"]
        description = spec["description"]
        if is_lockfile:
            spec = spec["lockfile"]

        context = {
            "request": request,
            "environment": environment,
            "entity": entity,
            "environment_name": name,
            "environment_description": description,
            "specification": yaml.dump(spec),
            "is_lockfile": is_lockfile,
            "namespaces": [environment.namespace],
        }

        return templates.TemplateResponse(request, "create.html", context)


@router_ui.get("/build/{build_id}/")
async def ui_get_build(
    build_id: int,
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    server=Depends(dependencies.get_server),
    entity=Depends(dependencies.get_entity),
):
    with conda_store.get_db() as db:
        build = api.get_build(db, build_id)
        if build is None:
            return templates.TemplateResponse(
                request,
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
            "spec": yaml.dump(build.specification.spec),
            "platform": get_installer_platform(),
        }

        return templates.TemplateResponse(request, "build.html", context)


@router_ui.get("/user/")
async def ui_get_user(
    request: Request,
    templates=Depends(dependencies.get_templates),
    conda_store=Depends(dependencies.get_conda_store),
    auth=Depends(dependencies.get_auth),
    entity=Depends(dependencies.get_entity),
):
    with conda_store.get_db() as db:
        if entity is None:
            return RedirectResponse(request.url_for("get_login_method"))

        entity_binding_permissions = auth.authorization.get_entity_binding_permissions(
            entity
        )

        orm_namespaces = auth.filter_namespaces(
            entity, api.list_namespaces(db, show_soft_deleted=False)
        )

        system_metrics = api.get_system_metrics(db)

        namespace_usage_metrics = auth.filter_namespaces(
            entity, api.get_namespace_metrics(db)
        )

        context = {
            "request": request,
            "username": entity.primary_namespace,
            "namespaces": orm_namespaces,
            "entity_binding_permissions": entity_binding_permissions,
            "system_metrics": system_metrics,
            "namespace_usage_metrics": namespace_usage_metrics,
        }
        return templates.TemplateResponse(request, "user.html", context)


@router_ui.get("/setting/")
@router_ui.get("/setting/{namespace}/")
@router_ui.get("/setting/{namespace}/{environment_name}/")
async def ui_get_setting(
    request: Request,
    templates=Depends(dependencies.get_templates),
    auth=Depends(dependencies.get_auth),
    conda_store=Depends(dependencies.get_conda_store),
    namespace: str = None,
    environment_name: str = None,
):
    if namespace is None:
        arn = ""
    elif environment_name is None:
        arn = namespace
    else:
        arn = f"{namespace}/{environment_name}"

    auth.authorize_request(
        request,
        arn,
        {Permissions.SETTING_READ},
        require=True,
    )

    api_setting_url = str(request.url_for("api_put_settings"))
    if namespace is not None:
        api_setting_url += f"{namespace}/"
    if environment_name is not None:
        api_setting_url += f"{environment_name}/"

    context = {
        "request": request,
        "namespace": namespace,
        "environment_name": environment_name,
        "api_settings_url": api_setting_url,
        "settings": conda_store.get_settings(
            namespace=namespace, environment_name=environment_name
        ),
    }
    return templates.TemplateResponse(request, "setting.html", context)
