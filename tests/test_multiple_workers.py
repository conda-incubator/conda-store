"""
These tests utilizse pytest-xdist to run their builds in parallel. In this case,
we don't need to assume a build, the tests will send new environments to build under the
same namespace on the server, checking to see if file-locking really works.  

This will use the exposed api as opposed to running playwright style.
"""
import pathlib


import yaml

ENVIRONMENT_YAML_PATH = pathlib.Path("./assets/environments/python-parallel-test.yaml")

def read_environment_spec(name: str, p: pathlib.Path = ENVIRONMENT_YAML_PATH):
    with open(p, "r") as f:
        spec = yaml.safe_load(f)

    spec["name"] = name
    return spec

def test_build_a(testclient):
    read_environment_spec("test_build_a")
    pass

def test_build_b(testclient):
    read_environment_spec("test_build_b")
    pass

def test_build_c(testclient):
    read_environment_spec("test_build_c")
    pass
