"""DYNAMICS metadata helpers."""

import shutil
from pathlib import Path

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/meta", tags=["meta"])


def _discover_gromacs_binary() -> str | None:
    candidate = settings.gromacs_executable()
    if Path(candidate).is_file():
        return candidate
    return shutil.which(candidate) or shutil.which("gmx") or shutil.which("gmx_mpi")


@router.get("/dynamics-summary")
async def dynamics_summary():
    return {
        "module": "dynamics",
        "gromacs_bin": _discover_gromacs_binary(),
        "features": {
            "gromacs_backend": True,
            "aex_engine": True,
            "validation_harness": True,
            "frontend_submit_flow": True,
        },
    }
