# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from fastapi.testclient import TestClient


def test_base_route(testclient):
    """The server should return the client app"""
    response = testclient.get("/")
    assert response.is_success
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text


def test_unknown_routes(testclient):
    """Rather than return a 404, the server should return the client app
    and let it handle unknown routes"""
    response = testclient.get("/foo")
    assert response.is_success
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text

    response = testclient.get("/foo/bar")
    assert response.is_success
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text


def test_not_found_route(testclient):
    """The /not-found route should also return the client app
    but with a 404 status code"""
    response = testclient.get("/not-found")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text


def test_route_outside_ui_app(testclient):
    """The server should not return the client app for a server-side route"""
    response = testclient.get("/favicon.ico")
    assert response.is_success
    assert response.headers["content-type"].startswith("image/")


def test_base_route_prefix(conda_store_server):
    conda_store_server.url_prefix = "/conda-store"
    testclient = TestClient(conda_store_server.init_fastapi_app())
    response = testclient.get("/conda-store")
    assert response.is_success
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text


def test_unknown_routes_prefix(conda_store_server):
    conda_store_server.url_prefix = "/conda-store"
    testclient = TestClient(conda_store_server.init_fastapi_app())

    response = testclient.get("/conda-store/foo")
    assert response.is_success
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text

    response = testclient.get("/conda-store/foo/bar")
    assert response.is_success
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text


def test_not_found_route_prefix(conda_store_server):
    conda_store_server.url_prefix = "/conda-store"
    testclient = TestClient(conda_store_server.init_fastapi_app())

    response = testclient.get("/conda-store/not-found")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text


def test_route_outside_ui_app_prefix(conda_store_server):
    """The server should not return the client app for a known route
    that is already mapped server-side"""
    conda_store_server.url_prefix = "/conda-store"
    testclient = TestClient(conda_store_server.init_fastapi_app())

    response = testclient.get("/favicon.ico")
    assert response.is_success
    assert response.headers["content-type"].startswith("image/")

    # test nonsense route
    response = testclient.get("/foo/bar")
    assert response.status_code == 404
    assert "condaStoreConfig" not in response.text


def test_ui_disabled(conda_store_server):
    conda_store_server.enable_ui = False
    testclient = TestClient(conda_store_server.init_fastapi_app())

    response = testclient.get("/")
    assert "condaStoreConfig" not in response.text

    response = testclient.get("/not-found")
    assert response.status_code == 404
    assert "condaStoreConfig" not in response.text

    response = testclient.get("/favicon.ico")
    assert response.status_code == 404
    assert "condaStoreConfig" not in response.text
