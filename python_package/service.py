"""DYNAMICS job paths and light validation (heavy work stays in workers / GROMACS)."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any, Dict

from app.config import settings
from app.core.storage import get_storage

from .estimator import RuntimeEstimator
from .gromacs_runner import DynamicsInputs


class DynamicsService:
    @classmethod
    def upload_root(cls) -> Path:
        return Path(settings.LOCAL_UPLOAD_ROOT)

    @classmethod
    def output_root(cls) -> Path:
        return Path(settings.DYNAMICS_OUTPUT_ROOT)

    @classmethod
    def job_upload_dir(cls, job_id: str) -> Path:
        p = cls.upload_root() / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def job_output_dir(cls, job_id: str) -> Path:
        return cls.output_root() / job_id

    @classmethod
    def output_zip_path(cls, job_id: str) -> Path:
        return cls.job_output_dir(job_id) / f"{job_id}_outputs.zip"

    @classmethod
    def aex_report_path(cls, job_id: str) -> Path:
        return cls.job_output_dir(job_id) / "aex_report.json"

    @classmethod
    def parse_and_estimate(cls, params_dict: Dict[str, Any]) -> Dict[str, Any]:
        field_names = {f.name for f in fields(DynamicsInputs)}
        clean = {k: v for k, v in params_dict.items() if k in field_names}
        inputs = DynamicsInputs(**clean)
        return RuntimeEstimator(inputs).estimate()

    @classmethod
    def persist_upload(cls, job_id: str, name: str, data: bytes) -> str:
        rel = f"{job_id}/{name}"
        return get_storage().write_bytes(rel, data)
