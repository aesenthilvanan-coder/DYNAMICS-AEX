"""Create database tables from ORM models (Postgres)."""

from app.config import settings
from app.core.db import get_engine
from app.db.base import Base

# Ensure all tables are registered on Base.metadata before create_all
import app.db.models  # noqa: F401


def init_database() -> None:
    if not settings.ENABLE_DATABASE:
        return
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
