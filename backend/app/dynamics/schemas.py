from typing import Any, Dict, Optional

from pydantic import BaseModel


class DynamicsJobRequest(BaseModel):
    """JSON fields mirror DynamicsInputs (file uploads handled separately)."""

    forcefield: str = "amber99sb-ildn"
    use_aex: bool = False


class DynamicsJobResponse(BaseModel):
    job_id: str
    status: str
    estimate: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    current_step: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
