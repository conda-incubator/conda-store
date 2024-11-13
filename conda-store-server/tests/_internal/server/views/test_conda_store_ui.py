# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest
from fastapi.testclient import TestClient


def assert_client_app(response):
    """A few checks that should all pass if the response is ok and contains
    the client app
    """
    assert response.is_success
    assert "text/html" in response.headers["content-type"]
    assert "condaStoreConfig" in response.text


class TestUIRoutes:
    url_prefix = "/"

    def full_route(self, route):
        if self.url_prefix == "/":
            return route
        else:
            return self.url_prefix + route

    @pytest.fixture
    def testclient(self, conda_store_server):
        conda_store_server.enable_ui = True
        conda_store_server.url_prefix = self.url_prefix
        return TestClient(conda_store_server.init_fastapi_app())

    def test_base_route(self, testclient):
        """The server should return the client app"""
        response = testclient.get(self.url_prefix)
        assert_client_app(response)

    def test_unknown_routes(self, testclient):
        """Rather than return a 404, the server should return the client app
        and let it handle unknown routes
        """
        response = testclient.get(self.full_route("/ui/foo"))
        assert_client_app(response)

        response = testclient.get(self.full_route("/ui/foo/bar"))
        assert_client_app(response)

    def test_not_found_route(self, testclient):
        """The /not-found route should also return the client app
        but with a 404 status code
        """
        response = testclient.get(self.full_route("/ui/not-found"))
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "condaStoreConfig" in response.text

    def test_route_outside_ui_app(self, testclient):
        """The server should not return the client app for a server-side
        route
        """
        response = testclient.get(self.full_route("/admin/"))
        assert response.is_success
        assert "condaStoreConfig" not in response.text

        response = testclient.get(self.full_route("/favicon.ico"))
        assert response.is_success
        assert response.headers["content-type"].startswith("image/")


def assert_not_found_not_client_app(response):
    assert response.status_code == 404
    assert "condaStoreConfig" not in response.text


class TestUIRoutesCustomPrefix(TestUIRoutes):
    url_prefix = "/conda-store"

    def test_unknown_route_outside_prefix(self, testclient):
        """The server should return a 404 for an unknown route outside
        the url prefix and should not return the client app
        """
        response = testclient.get("/ui/foo/bar")
        assert_not_found_not_client_app(response)


def test_ui_disabled(conda_store_server):
    """When the UI is disabled, the server should return 404s for
    all UI routes and should not return the client app
    """
    conda_store_server.enable_ui = False
    conda_store_server.url_prefix = "/"
    testclient = TestClient(conda_store_server.init_fastapi_app())

    response = testclient.get("/")
    assert_not_found_not_client_app(response)

    response = testclient.get("/ui/not-found")
    assert_not_found_not_client_app(response)

    response = testclient.get("/admin/")
    assert_not_found_not_client_app(response)

    response = testclient.get("/favicon.ico")
    assert_not_found_not_client_app(response)
