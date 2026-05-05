"""Celery tasks for DYNAMICS (canonical registration lives with the dynamics package)."""

from __future__ import annotations

import dataclasses
import logging

from app.config import settings
from app.core.celery_app import celery_app
from app.core.db import session_scope
from app.persistence.jobs import (
    mark_job_complete,
    mark_job_failed,
    mark_job_running,
    persist_dynamics_success,
)

from .gromacs_runner import DynamicsInputs, GROMACSRunner

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_dynamics_job", max_retries=2, time_limit=86400, queue="dynamics")
def run_dynamics_job(self, params_dict: dict):
    try:
        field_names = {f.name for f in dataclasses.fields(DynamicsInputs)}
        clean = {k: v for k, v in params_dict.items() if k in field_names}
        inputs = DynamicsInputs(**clean)
        if "output_dir" not in clean and settings.DYNAMICS_OUTPUT_ROOT.strip():
            inputs = dataclasses.replace(inputs, output_dir=settings.DYNAMICS_OUTPUT_ROOT.strip())
        jid = params_dict["job_id"]

        if settings.ENABLE_DATABASE:
            with session_scope() as db:
                mark_job_running(db, jid)

        runner = GROMACSRunner(inputs)

        def progress_cb(step: str, pct: int):
            self.update_state(state="PROGRESS", meta={"step": step, "progress": pct})

        result = runner.run(progress_callback=progress_cb)
        out = {
            "job_id": result.job_id,
            "success": result.success,
            "zip_path": result.zip_path,
            "simulated_ns": result.simulated_time_ns,
            "wall_time_s": result.wall_time_seconds,
            "aex_speedup": result.aex_speedup_achieved,
            "error": result.error_message,
        }
        if result.aex_report is not None:
            out["aex_report"] = result.aex_report

        if settings.ENABLE_DATABASE:
            if result.success:
                with session_scope() as db:
                    persist_dynamics_success(db, jid, out, inputs)
                    mark_job_complete(db, jid)
            else:
                with session_scope() as db:
                    mark_job_failed(db, jid, result.error_message or "dynamics failed")

        return out
    except Exception as e:
        logger.error("Dynamics worker failed: %s", e, exc_info=True)
        if settings.ENABLE_DATABASE and params_dict.get("job_id"):
            if self.request.retries >= self.max_retries:
                with session_scope() as db:
                    mark_job_failed(db, params_dict["job_id"], str(e))
        raise self.retry(exc=e, countdown=30)
