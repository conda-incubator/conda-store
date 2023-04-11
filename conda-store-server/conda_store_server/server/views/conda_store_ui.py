from fastapi import APIRouter, Request, Depends

from conda_store_server.server import dependencies

router_conda_store_ui = APIRouter(tags=["conda-store-ui"])


@router_conda_store_ui.get("/")
def get_conda_store_ui(
    request: Request,
    templates=Depends(dependencies.get_templates),
):
    context = {
        "request": request,
    }
    return templates.TemplateResponse("conda-store-ui.html", context)
