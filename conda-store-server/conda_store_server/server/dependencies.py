from fastapi import Request, Depends


def get_conda_store(request: Request):
    return request.state.conda_store


def get_server(request: Request):
    return request.state.server


def get_auth(request: Request):
    return request.state.authentication


def get_entity(request: Request, auth=Depends(get_auth)):
    return auth.authenticate_request(request)


def get_templates(request: Request):
    return request.state.templates
