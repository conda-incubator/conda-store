# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from fastapi import APIRouter, Depends, Request

from conda_store_server.server import dependencies


router_conda_store_ui = APIRouter(tags=["conda-store-ui"])

@router_conda_store_ui.get("/")
@router_conda_store_ui.get("/{full_path:path}")
async def get_conda_store_ui(
    request: Request,
    full_path: str,
    templates=Depends(dependencies.get_templates),
):
    context = {
        "request": request,
    }
    return templates.TemplateResponse("conda-store-ui.html", context)
