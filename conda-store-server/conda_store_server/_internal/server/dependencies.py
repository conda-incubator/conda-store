# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
from fastapi import Depends, Request


async def get_conda_store(request: Request):
    return request.state.conda_store


async def get_server(request: Request):
    return request.state.server


async def get_auth(request: Request):
    return request.state.authentication


async def get_entity(
    request: Request,
    auth=Depends(get_auth),
):
    """Get the token representing the user who made the request.

    Parameters
    ----------
    auth : auth.Authentication
        Authentication instance
    request : Request
        Raw starlette request

    Returns
    -------
    Optional[schema.AuthenticationToken]
        An authenticated token, if present; otherwise None
    """
    return auth.authenticate_request(request)


async def get_templates(request: Request):
    return request.state.templates
