"""DYNAMICS HTTP API (FastAPI router) — lives in the dynamics package."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse

from app.config import settings
from app.core.db import session_scope
from app.persistence.jobs import create_job_record

from .celery_tasks import run_dynamics_job
from .inprocess import get_status as inprocess_get_status
from .inprocess import has_job as inprocess_has_job
from .inprocess import job_count as inprocess_job_count
from .inprocess import submit as inprocess_submit
from .local_bootstrap import bootstrap_manifest, render_bootstrap_shell_script
from .schemas import JobStatusResponse
from .service import DynamicsService

router = APIRouter(prefix="/dynamics", tags=["DYNAMICS"])
service = DynamicsService()


def _discover_gromacs_binary() -> Optional[str]:
    candidate = settings.gromacs_executable()
    if Path(candidate).is_file():
        return candidate
    return shutil.which(candidate) or shutil.which("gmx") or shutil.which("gmx_mpi")


@router.post("/submit")
async def submit_dynamics_job(
    protein_pdb: UploadFile = File(..., description="Protein PDB file"),
    ligand_itp: Optional[UploadFile] = File(None, description="Ligand ITP topology"),
    ligand_mol2: Optional[UploadFile] = File(None, description="Ligand MOL2 file"),
    params: str = Form(..., description="JSON-encoded DynamicsInputs parameters"),
):
    job_id = str(uuid.uuid4())
    params_dict = json.loads(params)
    params_dict["job_id"] = job_id
    pdb_path = service.persist_upload(job_id, "input.pdb", await protein_pdb.read())
    params_dict["protein_pdb"] = pdb_path
    if ligand_itp:
        params_dict["ligand_itp"] = service.persist_upload(job_id, "ligand.itp", await ligand_itp.read())
    if ligand_mol2:
        params_dict["ligand_mol2"] = service.persist_upload(job_id, "ligand.mol2", await ligand_mol2.read())

    estimate = service.parse_and_estimate(params_dict)
    if settings.ENABLE_DATABASE:
        with session_scope() as db:
            create_job_record(db, job_id, "dynamics", metadata={"estimate": estimate})

    # Prefer Celery if broker is available; fallback to in-process thread in local/dev.
    try:
        run_dynamics_job.apply_async(args=[params_dict], task_id=job_id)
        mode = "celery"
    except Exception:
        inprocess_submit(job_id, params_dict)
        mode = "inprocess"

    return {"job_id": job_id, "status": "queued", "estimate": estimate, "mode": mode}


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    # If job was executed in-process (or broker was down at submit time), serve that status.
    if inprocess_has_job(job_id):
        st = inprocess_get_status(job_id) or {}
        state = (st.get("state") or "PENDING").upper()
        meta = st.get("meta") or {}
        if state == "PENDING":
            return JobStatusResponse(job_id=job_id, status="pending", progress=int(meta.get("progress", 0)))
        if state == "PROGRESS":
            return JobStatusResponse(
                job_id=job_id,
                status="running",
                progress=int(meta.get("progress", 0)),
                current_step=str(meta.get("step", "")),
            )
        if state == "SUCCESS":
            return JobStatusResponse(job_id=job_id, status="complete", progress=100, result=st.get("result"))
        if state == "FAILURE":
            return JobStatusResponse(job_id=job_id, status="failed", progress=100, error=str(st.get("error") or ""))
        return JobStatusResponse(job_id=job_id, status=state.lower(), progress=int(meta.get("progress", 0)))

    from app.core.celery_app import celery_app

    result = celery_app.AsyncResult(job_id)
    if result.state == "PENDING":
        return JobStatusResponse(job_id=job_id, status="pending", progress=0)
    if result.state == "PROGRESS":
        meta = result.info or {}
        return JobStatusResponse(
            job_id=job_id,
            status="running",
            progress=meta.get("progress", 0),
            current_step=meta.get("step", ""),
        )
    if result.state == "SUCCESS":
        return JobStatusResponse(job_id=job_id, status="complete", progress=100, result=result.result)
    if result.state == "FAILURE":
        return JobStatusResponse(job_id=job_id, status="failed", error=str(result.info))
    return JobStatusResponse(job_id=job_id, status=result.state.lower(), progress=0)


@router.get("/jobs/{job_id}/download")
async def download_outputs(job_id: str):
    zip_path = service.output_zip_path(job_id)
    if not zip_path.is_file():
        raise HTTPException(404, f"Output file not found for job {job_id}")
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=f"caly360_dynamics_{job_id}.zip",
    )


@router.get("/jobs/{job_id}/aex-report")
async def get_aex_report(job_id: str):
    report_path = service.aex_report_path(job_id)
    if not report_path.is_file():
        raise HTTPException(404, "AEX report not found (may not be an AEX job)")
    with open(report_path) as f:
        return json.load(f)


@router.get("/health-md")
async def dynamics_health():
    return {"gromacs": _discover_gromacs_binary()}


@router.get("/health-execution")
async def dynamics_execution_health():
    from app.core.celery_app import celery_app

    gmx = _discover_gromacs_binary()
    broker = None
    try:
        # cheap connectivity check
        celery_app.connection().ensure_connection(max_retries=1, timeout=0.5)
        broker = "ok"
    except Exception as e:
        broker = f"error: {e!s}"
    return {
        "gromacs": gmx,
        "broker": broker,
        "inprocess_jobs": inprocess_job_count(),
    }


@router.get("/local-bootstrap.json")
async def dynamics_local_bootstrap_json():
    """Metadata for the Simulate flow: what to download and how to run workers locally."""
    return bootstrap_manifest()


@router.get("/local-bootstrap.sh")
async def dynamics_local_bootstrap_sh():
    """Downloadable shell script: Docker build/up for MD stack + GROMACS hints."""
    body = render_bootstrap_shell_script()
    return PlainTextResponse(
        body,
        media_type="text/x-shellscript",
        headers={"Content-Disposition": 'attachment; filename="caly360-dynamics-local-setup.sh"'},
    )
