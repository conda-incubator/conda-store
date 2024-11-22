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


async def get_entity(request: Request, auth=Depends(get_auth)):
    return auth.authenticate_request(request)


async def get_templates(request: Request):
    return request.state.templates


async def get_url_prefix(request: Request, server=Depends(get_server)):
    return server.url_prefix
