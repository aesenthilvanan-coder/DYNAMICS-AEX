"""DYNAMICS FastAPI application."""

import logging
from contextlib import asynccontextmanager
import shutil

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.config import settings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENABLE_DATABASE:
        from app.db.bootstrap import init_database

        init_database()
    yield


app = FastAPI(
    title="Caly360 DYNAMICS",
    description="Molecular dynamics execution with GROMACS backend and optional AEX adaptive execution.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

if settings.ENABLE_METRICS:
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/ready")
async def ready():
    """Readiness probe: fails when ENABLE_DATABASE is true but Postgres is unreachable."""
    if not settings.ENABLE_DATABASE:
        return {"status": "ready", "database": "not_required"}
    from sqlalchemy import text

    from app.core.db import get_engine

    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"database_unavailable: {e!s}")
    return {"status": "ready", "database": "ok"}


@app.get("/health")
async def health():
    body: dict = {
        "status": "ok",
        "version": "1.0.0",
        "database": "disabled",
        "storage_backend": settings.STORAGE_BACKEND,
        "gromacs_bin": shutil.which("gmx") or shutil.which("gmx_mpi") or settings.gromacs_executable(),
        "module": "dynamics",
    }
    if settings.ENABLE_DATABASE:
        try:
            from sqlalchemy import text
            from app.core.db import get_engine

            with get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
            body["database"] = "ok"
        except Exception as e:
            body["database"] = f"error: {e!s}"
            body["status"] = "degraded"
    return body
