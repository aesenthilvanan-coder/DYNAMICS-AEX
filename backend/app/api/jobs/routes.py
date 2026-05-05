"""Aggregate job discovery (Celery task id == client job id)."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}/status")
async def unified_job_status(job_id: str):
    try:
        from app.core.celery_app import celery_app

        r = celery_app.AsyncResult(job_id)
        out = {
            "job_id": job_id,
            "celery_state": r.state,
            "ready": r.ready(),
            "successful": r.successful(),
            "result": r.result if r.successful() else None,
            "error": str(r.info) if r.failed() else None,
        }
    except Exception as e:
        out = {
            "job_id": job_id,
            "celery_state": "unavailable",
            "ready": False,
            "successful": False,
            "result": None,
            "error": str(e),
        }
    if settings.ENABLE_DATABASE:
        from app.core.db import session_scope
        from app.persistence.jobs import get_job_row

        with session_scope() as db:
            job = get_job_row(db, job_id)
            if job:
                out["database_job"] = {
                    "job_type": job.job_type,
                    "status": job.status,
                    "error_message": job.error_message,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "metadata": job.job_metadata,
                }
    return out


@router.get("")
async def jobs_index():
    return {
        "dynamics": "POST /api/v1/dynamics/submit → poll GET /api/v1/dynamics/jobs/{job_id}",
        "unified": "GET /api/v1/jobs/{job_id}/status",
        "database": "Set ENABLE_DATABASE=true and run the API with Postgres; tables are created on startup.",
        "storage": "STORAGE_BACKEND=local (default) or s3 with S3_BUCKET (+ optional S3_ENDPOINT_URL for MinIO).",
    }
