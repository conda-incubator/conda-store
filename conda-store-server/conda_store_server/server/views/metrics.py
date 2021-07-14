from flask import Blueprint, make_response

from conda_store_server import api
from conda_store_server.server.utils import get_conda_store


app_metrics = Blueprint("metrics", __name__)


@app_metrics.route("/metrics")
def prometheus_metrics():
    conda_store = get_conda_store()
    metrics = api.get_metrics(conda_store.db)
    response = make_response('\n'.join(f'conda_store_{key} {value}' for key, value in metrics.items()))
    response.mimetype = "text/plain"
    return response
