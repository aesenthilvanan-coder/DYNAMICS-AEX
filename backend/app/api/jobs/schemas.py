from pydantic import BaseModel
from typing import Optional, Any


class JobRef(BaseModel):
    job_id: str
    status: str
    detail: Optional[Any] = None
