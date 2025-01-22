from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request

from conda_store_server import api
from conda_store_server._internal import orm, schema
from conda_store_server._internal.environment import filter_environments
from conda_store_server._internal.server import dependencies
from conda_store_server._internal.server.pagination import (
    Cursor,
    CursorPaginatedArgs,
    OrderingMetadata,
    paginate,
)
from conda_store_server.conda_store import CondaStore
from conda_store_server.server.auth import Authentication
from conda_store_server.server.schema import AuthenticationToken

router_api = APIRouter(
    tags=["api"],
    prefix="/api/v2",
)


@router_api.get(
    "/environment/",
    response_model=schema.APIV2ListEnvironment,
    response_model_exclude={"data": {"__all__": {"current_build"}}},
)
async def api_list_environments_v2(
    request: Request,
    auth: Authentication = Depends(dependencies.get_auth),
    conda_store: CondaStore = Depends(dependencies.get_conda_store),
    entity: AuthenticationToken = Depends(dependencies.get_entity),
    paginated_args: CursorPaginatedArgs = Depends(
        dependencies.get_cursor_paginated_args
    ),
    cursor: Cursor = Depends(dependencies.get_cursor),
    artifact: Optional[schema.BuildArtifactType] = None,
    jwt: Optional[str] = None,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    packages: Optional[List[str]] = Query([]),
    search: Optional[str] = None,
    status: Optional[schema.BuildStatus] = None,
) -> schema.APIListEnvironment:
    """Retrieve a list of environments.

    Parameters
    ----------
    auth : Authentication
        Authentication instance for the request. Used to get role bindings
        and filter environments returned to those visible by the user making
        the request
    entity : AuthenticationToken
        Token of the user making the request
    paginated_args : CursorPaginatedArgs
        Arguments for controlling pagination of the response
    conda_store : app.CondaStore
        The running conda store application
    search : Optional[str]
        If specified, filter by environment names or namespace names containing the
        search term
    namespace : Optional[str]
        If specified, filter by environments in the given namespace
    name : Optional[str]
        If specified, filter by environments with the given name
    status : Optional[schema.BuildStatus]
        If specified, filter by environments with the given status
    packages : Optional[List[str]]
        If specified, filter by environments containing the given package name(s)
    artifact : Optional[schema.BuildArtifactType]
        If specified, filter by environments with the given BuildArtifactType
    jwt : Optional[auth_schema.AuthenticationToken]
        If specified, retrieve only the environments accessible to this token; that is,
        only return environments that the user has 'admin', 'editor', and 'viewer'
        role bindings for.

    Returns
    -------
    schema.APIListEnvironment
        Paginated JSON response containing the requested environments. Cursor-based pagination
        is used.

        Note that the Environment objects returned here have their `current_build` fields omitted
        to keep the repsonse size down; these fields otherwise drastically increase the response
        size.
    """
    with conda_store.get_db() as db:
        if jwt:
            # Fetch the environments visible to the supplied token
            role_bindings = auth.entity_bindings(
                AuthenticationToken.model_validate(
                    auth.authentication.decrypt_token(jwt)
                )
            )
        else:
            role_bindings = None

        query = api.list_environments(
            db,
            search=search,
            namespace=namespace,
            name=name,
            status=status,
            packages=packages,
            artifact=artifact,
            show_soft_deleted=False,
            role_bindings=role_bindings,
        )

        # Filter by environments that the user who made the query has access to
        query = filter_environments(
            query=query,
            role_bindings=auth.entity_bindings(entity),
        )

        paginated, next_cursor, count = paginate(
            query=query,
            ordering_metadata=OrderingMetadata(
                valid_orderings=["namespace", "name"],
                column_names=["namespace.name", "name"],
                column_objects=[orm.Namespace.name, orm.Environment.name],
            ),
            cursor=cursor,
            sort_by=paginated_args.sort_by,
            order=paginated_args.order,
            limit=paginated_args.limit,
        )

        return schema.APIV2ListEnvironment(
            data=paginated,
            status="ok",
            cursor=next_cursor.dump(),
            count=count,
        )
