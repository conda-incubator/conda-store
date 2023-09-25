from conda_store_server.server import dependencies
from fastapi import APIRouter, Depends, Request

router_conda_store_ui = APIRouter(tags=["conda-store-ui"])


@router_conda_store_ui.get("/")
async def get_conda_store_ui(
    request: Request,
    templates=Depends(dependencies.get_templates),
):
    context = {
        "request": request,
    }
    return templates.TemplateResponse("conda-store-ui.html", context)
