"""Celery application."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "caly360",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.dynamics.celery_tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_routes={
        "run_dynamics_job": {"queue": "dynamics"},
    },
)
