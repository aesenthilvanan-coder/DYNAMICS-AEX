"""In-process execution fallback for DYNAMICS jobs.

Used only when Celery broker is unavailable in local/dev runs.
This lets the frontend submit + poll without requiring Redis/Celery.
"""

from __future__ import annotations

import dataclasses
import logging
import threading
import time
from typing import Any, Dict, Optional

from app.config import settings

from .gromacs_runner import DynamicsInputs, GROMACSRunner

logger = logging.getLogger(__name__)


_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


def has_job(job_id: str) -> bool:
    with _lock:
        return job_id in _jobs


def job_count() -> int:
    with _lock:
        return len(_jobs)


def get_status(job_id: str) -> Optional[dict[str, Any]]:
    with _lock:
        j = _jobs.get(job_id)
        return dict(j) if j else None


def submit(job_id: str, params_dict: dict) -> None:
    with _lock:
        _jobs[job_id] = {"state": "PENDING", "meta": {"progress": 0, "step": ""}, "result": None, "error": None}

    t = threading.Thread(target=_run_job_thread, args=(job_id, params_dict), daemon=True)
    t.start()


def _set_state(job_id: str, state: str, *, meta: Optional[dict] = None, result: Any = None, error: str | None = None):
    with _lock:
        j = _jobs.setdefault(job_id, {})
        j["state"] = state
        if meta is not None:
            j["meta"] = meta
        if result is not None:
            j["result"] = result
        if error is not None:
            j["error"] = error


def _run_job_thread(job_id: str, params_dict: dict) -> None:
    try:
        _set_state(job_id, "PROGRESS", meta={"progress": 1, "step": "starting"})

        field_names = {f.name for f in dataclasses.fields(DynamicsInputs)}
        clean = {k: v for k, v in params_dict.items() if k in field_names}
        inputs = DynamicsInputs(**clean)
        if "output_dir" not in clean and settings.DYNAMICS_OUTPUT_ROOT.strip():
            inputs = dataclasses.replace(inputs, output_dir=settings.DYNAMICS_OUTPUT_ROOT.strip())

        runner = GROMACSRunner(inputs)

        def progress_cb(step: str, pct: int):
            _set_state(job_id, "PROGRESS", meta={"progress": int(pct), "step": step})

        # mark running
        _set_state(job_id, "PROGRESS", meta={"progress": 2, "step": "queued (in-process)"})
        time.sleep(0.05)

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

        if result.success:
            _set_state(job_id, "SUCCESS", meta={"progress": 100, "step": "complete"}, result=out)
        else:
            _set_state(job_id, "FAILURE", meta={"progress": 100, "step": "failed"}, error=result.error_message or "failed")
    except Exception as e:
        logger.error("In-process dynamics job failed: %s", e, exc_info=True)
        _set_state(job_id, "FAILURE", meta={"progress": 100, "step": "failed"}, error=str(e))

