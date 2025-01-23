# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from typing import Optional, TypedDict

from fastapi import Depends, Query, Request

from conda_store_server._internal.server.pagination import (
    Cursor,
    CursorPaginatedArgs,
    Ordering,
)


async def get_conda_store(request: Request):
    return request.state.conda_store


async def get_server(request: Request):
    return request.state.server


async def get_auth(request: Request):
    return request.state.authentication


async def get_entity(request: Request, auth=Depends(get_auth)):
    return auth.authenticate_request(request)


async def get_templates(request: Request):
    return request.state.templates


async def get_url_prefix(request: Request, server=Depends(get_server)):
    return server.url_prefix


def get_cursor(cursor: str | None = None) -> Cursor:
    return Cursor.load(cursor)


def get_cursor_paginated_args(
    order: Ordering = Ordering.ASCENDING,
    limit: int | None = None,
    sort_by: list[str] = Query([]),
    server=Depends(get_server),
) -> CursorPaginatedArgs:
    return CursorPaginatedArgs(
        limit=server.max_page_size if limit is None else limit,
        order=order,
        sort_by=sort_by,
    )


class PaginatedArgs(TypedDict):
    """Dictionary type holding information about paginated requests."""

    limit: int
    offset: int
    sort_by: list[str]
    order: str


def get_paginated_args(
    page: int = 1,
    order: Optional[str] = None,
    size: Optional[int] = None,
    sort_by: list[str] = Query([]),
    server=Depends(get_server),
) -> PaginatedArgs:
    if size is None:
        size = server.max_page_size
    size = min(size, server.max_page_size)
    offset = (page - 1) * size
    return {
        "limit": size,
        "offset": offset,
        "sort_by": sort_by,
        "order": order,
    }
