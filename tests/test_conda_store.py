import pytest


def test_conda_store_update_storage_metrics(conda_store):
    conda_store.update_storage_metrics()


def test_conda_store_update_conda_channels(conda_store):
    conda_store.update_conda_channels()


@pytest.mark.parametrize('environment', [
    'tests/assets/environments/conda-store.yaml',
    'tests/assets/environments/data-science.yaml',
    'tests/assets/environments/jupyterlab.yaml',
    'tests/assets/environments/web-development.yaml',
])
def test_conda_store_register_specification(conda_store, environment):
    conda_store.register_environment(environment)
    build = conda_store.claim_build()
