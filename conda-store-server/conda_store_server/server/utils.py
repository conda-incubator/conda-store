from fastapi import Request


def get_conda_store(request: Request):
    return request.state.conda_store


def get_server(request: Request):
    return request.state.server


def get_auth(request: Request):
    return request.state.authentication
