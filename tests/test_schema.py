import pytest
import yaml

from conda_store import schema


@pytest.mark.parametrize('environment_filename', [
    'tests/assets/environments/conda-store.yaml',
    'tests/assets/environments/jupyterlab.yaml',
    'tests/assets/environments/data-science.yaml',
    'tests/assets/environments/web-development.yaml',
])
def test_schema_environment(environment_filename):
    with open(environment_filename) as f:
        data = yaml.safe_load(f)
    schema.CondaSpecification.parse_obj(data)
