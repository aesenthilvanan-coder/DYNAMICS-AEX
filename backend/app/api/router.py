from fastapi import APIRouter, Depends

from app.api.dynamics.routes import router as dynamics_router
from app.api.jobs.routes import router as jobs_router
from app.dependencies import verify_api_key_if_configured

router = APIRouter(dependencies=[Depends(verify_api_key_if_configured)])
router.include_router(dynamics_router)
router.include_router(jobs_router)
