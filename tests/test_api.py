from conda_store import api


def test_api_list_conda_packages(conda_store, limit=100):
    packages = api.list_conda_packages(conda_store.db, limit=limit)
    assert len(packages) == limit


def test_api_get_metrics(conda_store):
    metrics = api.get_metrics(conda_store.db)
    assert {'free', 'total', 'disk_usage', 'used', 'percent', 'total_completed_builds', 'total_environments'} == set(metrics.keys())
