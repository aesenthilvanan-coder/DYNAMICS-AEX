"""Shim: Celery task is registered from ``app.dynamics.celery_tasks``."""

from app.dynamics.celery_tasks import run_dynamics_job

__all__ = ["run_dynamics_job"]
