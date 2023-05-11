import tempfile
import pathlib

from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates


def test_conda_store_server_enable_ui(conda_store_server):
    conda_store_server.enable_ui = False
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/")
    assert response.status_code == 404

    conda_store_server.enable_ui = True
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/")
    assert response.status_code == 200


def test_conda_store_server_enable_api(conda_store_server):
    conda_store_server.enable_api = False
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/api/v1/")
    assert response.status_code == 404

    conda_store_server.enable_api = True
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/api/v1/")
    assert response.status_code == 200


def test_conda_store_server_enable_registry(conda_store_server):
    conda_store_server.enable_registry = False
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/v2/")
    assert response.status_code == 404

    conda_store_server.enable_registry = True
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/v2/")
    assert response.status_code == 401  # unauthorized


def test_conda_store_server_enable_metrics(conda_store_server):
    conda_store_server.enable_metrics = False
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/metrics")
    assert response.status_code == 404

    conda_store_server.enable_metrics = True
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/metrics")
    assert response.status_code == 200


def test_conda_store_server_url_prefix(conda_store_server):
    conda_store_server.url_prefix = "/a/test/prefix/"
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307

    response = client.get("/a/test/prefix/", follow_redirects=False)
    assert response.status_code == 200

    conda_store_server.url_prefix = "/"
    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200


def test_conda_store_server_templates(conda_store_server):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)

        templates = Jinja2Templates(directory=str(tmpdir))

        content = b"<h1>Hello World {{ test_variable }}</h1>"
        with (tmpdir / "home.html").open("wb") as f:
            f.write(content)

        conda_store_server.templates = templates
        conda_store_server.template_vars = {"test_variable": "Test"}
        client = TestClient(conda_store_server.init_fastapi_app())
        response = client.get("/admin/")
        assert response.status_code == 200
        assert response.content == b"<h1>Hello World Test</h1>"


def test_conda_store_server_authentication_class(conda_store_server):
    from conda_store_server.server.auth import DummyAuthentication

    class MyAuthentication(DummyAuthentication):
        password = "helloworld"

    conda_store_server.authentication_class = MyAuthentication
    conda_store_server.initialize()

    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.post(
        "/login/", json={"username": "username", "password": "password"}
    )
    assert response.status_code == 403

    response = client.post(
        "/login/", json={"username": "username", "password": "helloworld"}
    )
    assert response.status_code == 200
