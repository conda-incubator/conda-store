from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from conda_store_server import api
from conda_store_server.server import dependencies


router_metrics = APIRouter(tags=["metrics"])


@router_metrics.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics(
    conda_store=Depends(dependencies.get_conda_store),
):
    metrics = api.get_metrics(conda_store.db)
    return "\n".join(f"conda_store_{key} {value}" for key, value in metrics.items())


@router_metrics.get("/celery")
def trigger_task(conda_store=Depends(dependencies.get_conda_store)):
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
