from flask import Blueprint, make_response

from conda_store_server import api
from conda_store_server.server.utils import get_conda_store


app_metrics = Blueprint("metrics", __name__)


@app_metrics.route("/metrics")
def prometheus_metrics():
    conda_store = get_conda_store()
    metrics = api.get_metrics(conda_store.db)
    response = make_response(
        "\n".join(f"conda_store_{key} {value}" for key, value in metrics.items())
    )
    response.mimetype = "text/plain"
    return response


@app_metrics.route("/celery")
def trigger_task():
    conda_store = get_conda_store()
    conda_store.celery_app

    def get_celery_worker_status(app):
        i = app.control.inspect()
        availability = i.ping()
        stats = i.stats()
        registered_tasks = i.registered()
        active_tasks = i.active()
        scheduled_tasks = i.scheduled()
        result = {
            "availability": availability,
            "stats": stats,
            "registered_tasks": registered_tasks,
            "active_tasks": active_tasks,
            "scheduled_tasks": scheduled_tasks,
        }
        return result

    return get_celery_worker_status(conda_store.celery_app)
