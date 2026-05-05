"""Dependency injection for FastAPI routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, Optional

from fastapi import Header, HTTPException

from app.config import Settings, settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
else:
    Session = Any


async def verify_api_key_if_configured(
    authorization: Optional[str] = Header(None),
) -> None:
    secret = (settings.API_KEY or "").strip()
    if not secret:
        return
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization: Bearer <API_KEY>",
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != secret:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization: Bearer <API_KEY>",
        )


def get_settings() -> Settings:
    return settings


def get_db() -> Generator[Session, None, None]:
    from app.core.db import get_session_factory

    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
