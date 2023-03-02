"""
These tests utilizse pytest-xdist to run their builds in parallel. In this case,
we don't need to assume a build, the tests will send new environments to build under the
same namespace on the server, checking to see if file-locking really works.  

This will use the exposed api as opposed to running playwright style.
"""
import json
import pathlib
import uuid

import yaml

from conda_store_server import schema

ENVIRONMENT_YAML_PATH = pathlib.Path("./assets/environments/python-parallel-test.yaml")


def read_environment_spec(name: str, p: pathlib.Path = ENVIRONMENT_YAML_PATH):
    with open(p, "r") as f:
        spec = yaml.safe_load(f)

    spec["name"] = name
    return json.dumps(spec)

#@pytest.mark.dependency(depends=['test_delete_build_auth'])
#def test_parallel_specification_build_auth(testclient):
#    namespace = "default"
#    envs = {}
#    env_a = f"pytest-{uuid.uuid4()}"
#    env_b = f"pytest-{uuid.uuid4()}"
#
#    testclient.login()
#
#    for e in (env_a, env_b):
#        envs[e] = {"namespace": namespace, "specification": read_environment_spec(e)}
#
#        response = testclient.post("api/v1/specification", envs[e])
#        response.raise_for_status()
#
#        r = schema.APIPostSpecification.parse_obj(response.json())
#        assert r.status == schema.APIStatus.OK
#        envs[e] = r
#
#    for e in envs:
#        # check for the given build
#        response = testclient.get(f"api/v1/build/{envs[e].data.build_id}")
#        response.raise_for_status()
#
#        r = schema.APIGetBuild.parse_obj(response.json())
#        assert r.status == schema.APIStatus.OK
#        assert r.data.specification.name == e
#
#        # check for the given environment
#        response = testclient.get(f"api/v1/environment/{namespace}/{e}")
#        response.raise_for_status()
#
#        r = schema.APIGetEnvironment.parse_obj(response.json())
#        assert r.data.namespace.name == namespace
