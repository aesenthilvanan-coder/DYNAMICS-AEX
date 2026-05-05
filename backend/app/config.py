"""Caly360 Application Configuration."""

import json
import os
import shutil
from pathlib import Path
from typing import List, Literal

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:
    class SettingsConfigDict(dict):
        pass

    class BaseSettings:
        model_config = SettingsConfigDict()

        def __init__(self, **kwargs):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                default = getattr(self.__class__, name, None)
                raw = kwargs.get(name, os.environ.get(name, default))
                setattr(self, name, self._coerce(raw, default))

        @staticmethod
        def _coerce(raw, default):
            if isinstance(default, bool):
                if isinstance(raw, str):
                    return raw.strip().lower() in {"1", "true", "yes", "on"}
                return bool(raw)
            if isinstance(default, int) and not isinstance(default, bool):
                try:
                    return int(raw)
                except Exception:
                    return default
            if isinstance(default, float):
                try:
                    return float(raw)
                except Exception:
                    return default
            if isinstance(default, list):
                if isinstance(raw, str):
                    text = raw.strip()
                    if not text:
                        return []
                    if text.startswith("["):
                        try:
                            return json.loads(text)
                        except Exception:
                            pass
                    return [part.strip() for part in text.split(",") if part.strip()]
                return list(raw) if raw is not None else []
            return raw


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Caly360"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    ENABLE_DATABASE: bool = False

    DATABASE_URL: str = "postgresql://caly360:password@db:5432/caly360"

    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    OUTPUT_BASE_DIR: str = "/tmp/caly360_outputs"
    DYNAMICS_OUTPUT_ROOT: str = "/tmp/caly360_md"

    API_KEY: str = ""

    ENABLE_METRICS: bool = False

    GROMACS_BIN: str = ""

    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_UPLOAD_ROOT: str = "/tmp/caly360_uploads"
    S3_BUCKET: str = ""
    S3_PREFIX: str = "caly360"
    S3_ENDPOINT_URL: str = ""
    AWS_REGION: str = "us-east-1"

    def gromacs_executable(self) -> str:
        s = self.GROMACS_BIN.strip()
        if s:
            return s
        bundled = (
            Path(__file__).resolve().parents[2]
            / ".tools"
            / "mamba-root"
            / "envs"
            / "gmx"
            / "bin"
            / "gmx"
        )
        if bundled.is_file():
            return str(bundled)
        return shutil.which("gmx") or shutil.which("gmx_mpi") or "gmx"


settings = Settings()
