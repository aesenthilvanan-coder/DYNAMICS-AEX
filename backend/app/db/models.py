"""ORM models aligned with migrations/versions/001_initial.sql."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    job_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)


class DynamicsResultRow(Base):
    __tablename__ = "dynamics_results"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    simulated_time_ns: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wall_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    use_aex: Mapped[bool] = mapped_column(Boolean, default=False)
    aex_speedup: Mapped[float] = mapped_column(Float, default=1.0)
    output_zip_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trajectory_xtc_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    energy_edr_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performance_ns_per_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    aex_report: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
