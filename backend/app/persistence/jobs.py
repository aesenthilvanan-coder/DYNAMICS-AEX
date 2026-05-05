"""Job and result persistence (Postgres)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.db.models import DynamicsResultRow, Job


def _uid(job_id: str) -> uuid.UUID:
    return uuid.UUID(job_id)


def create_job_record(
    db: Session,
    job_id: str,
    job_type: str,
    *,
    celery_task_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    db.add(
        Job(
            id=_uid(job_id),
            job_type=job_type,
            status="pending",
            celery_task_id=celery_task_id or job_id,
            job_metadata=metadata or {},
        )
    )


def mark_job_running(db: Session, job_id: str) -> None:
    row = db.get(Job, _uid(job_id))
    if row:
        row.status = "running"
        row.updated_at = datetime.now(timezone.utc)


def mark_job_complete(db: Session, job_id: str) -> None:
    row = db.get(Job, _uid(job_id))
    if row:
        row.status = "complete"
        row.completed_at = datetime.now(timezone.utc)
        row.updated_at = row.completed_at


def mark_job_failed(db: Session, job_id: str, message: str) -> None:
    row = db.get(Job, _uid(job_id))
    if row:
        row.status = "failed"
        row.error_message = message[:8000] if message else None
        row.completed_at = datetime.now(timezone.utc)
        row.updated_at = row.completed_at


def persist_dynamics_success(db: Session, job_id: str, payload: dict, inputs: object) -> None:
    """payload: worker return dict; inputs: DynamicsInputs-like with use_aex."""
    jid = _uid(job_id)
    db.add(
        DynamicsResultRow(
            job_id=jid,
            simulated_time_ns=payload.get("simulated_ns"),
            wall_time_seconds=payload.get("wall_time_s"),
            use_aex=bool(getattr(inputs, "use_aex", False)),
            aex_speedup=float(payload.get("aex_speedup") or 1.0),
            output_zip_path=payload.get("zip_path"),
            aex_report=payload.get("aex_report"),
        )
    )


def get_job_row(db: Session, job_id: str) -> Optional[Job]:
    return db.get(Job, _uid(job_id))
