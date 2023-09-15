import pathlib
import tempfile

import pytest
from conda_store_server import schema
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient


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


def test_conda_store_server_additional_routes(conda_store_server):
    def a_route(a: str, b: str):
        return {"data": f"Hello World {a} {b}"}

    conda_store_server.additional_routes = [
        (
            "/a/path/to/another/",
            "get",
            a_route,
        )
    ]

    client = TestClient(conda_store_server.init_fastapi_app())
    response = client.get("/a/path/to/another/", params={"a": "c", "b": "d"})
    assert response.status_code == 200
    assert response.json() == {"data": "Hello World c d"}


def test_conda_store_settings_conda_channels_packages_validate_valid(db, conda_store):
    conda_store.set_settings(
        db,
        data={
            "conda_allowed_channels": ["conda-forge"],
            "conda_included_packages": ["ipykernel"],
            "conda_required_packages": ["flask"],
            "pypi_included_packages": ["scipy"],
            "pypi_required_packages": ["numpy"],
        },
    )

    global_specification = conda_store.validate_specification(
        db,
        conda_store,
        namespace="default",
        specification=schema.CondaSpecification(
            name="test",
            channels=["conda-forge"],
            dependencies=[
                "flask",
                {"pip": ["numpy"]},
            ],
        ),
    )
    assert global_specification.channels == ["conda-forge"]
    assert sorted(global_specification.dependencies, key=lambda i: str(i)) == [
        "flask",
        "ipykernel",
        schema.CondaSpecificationPip(pip=["numpy", "scipy"]),
    ]

    conda_store.set_settings(
        db,
        namespace="default",
        data={
            "conda_allowed_channels": ["conda-forge"],
            "conda_included_packages": ["ipykernel", "pandas"],
            "conda_required_packages": ["flask"],
            "pypi_included_packages": ["scipy"],
            "pypi_required_packages": ["numpy"],
        },
    )

    namespace_specification = conda_store.validate_specification(
        db,
        conda_store,
        namespace="default",
        specification=schema.CondaSpecification(
            name="test",
            channels=["conda-forge"],
            dependencies=[
                "flask",
                {"pip": ["numpy"]},
            ],
        ),
    )
    assert namespace_specification.channels == ["conda-forge"]
    assert sorted(namespace_specification.dependencies, key=lambda i: str(i)) == [
        "flask",
        "ipykernel",
        "pandas",
        schema.CondaSpecificationPip(pip=["numpy", "scipy"]),
    ]

    conda_store.set_settings(
        db,
        namespace="default",
        environment_name="test",
        data={
            "conda_allowed_channels": ["conda-forge"],
            "conda_included_packages": ["ipykernel", "asdf"],
            "conda_required_packages": ["flask"],
            "pypi_included_packages": ["scipy"],
            "pypi_required_packages": ["numpy"],
        },
    )

    environment_specification = conda_store.validate_specification(
        db,
        conda_store,
        namespace="default",
        specification=schema.CondaSpecification(
            name="test",
            channels=["conda-forge"],
            dependencies=[
                "flask",
                {"pip": ["numpy"]},
            ],
        ),
    )
    assert environment_specification.channels == ["conda-forge"]
    assert sorted(environment_specification.dependencies, key=lambda i: str(i)) == [
        "asdf",
        "flask",
        "ipykernel",
        schema.CondaSpecificationPip(pip=["numpy", "scipy"]),
    ]

    # not allowed channel name
    with pytest.raises(ValueError):
        conda_store.validate_specification(
            db,
            conda_store,
            namespace="default",
            specification=schema.CondaSpecification(
                name="test",
                channels=["bad-channel"],
                dependencies=["flask", {"pip": ["numpy"]}],
            ),
        )

    # missing required conda package
    with pytest.raises(ValueError):
        conda_store.validate_specification(
            db,
            conda_store,
            namespace="default",
            specification=schema.CondaSpecification(
                name="test", channels=["conda-forge"], dependencies=[{"pip": ["numpy"]}]
            ),
        )

    # missing required pip package
    with pytest.raises(ValueError):
        conda_store.validate_specification(
            db,
            conda_store,
            namespace="default",
            specification=schema.CondaSpecification(
                name="test", channels=["conda-forge"], dependencies=["flask"]
            ),
        )
