"""Compatibility re-exports; canonical implementation is ``app.dynamics.failures``."""

from app.dynamics.failures import (
    FailureClass,
    FailureReport,
    detect_failures,
    summarize_failures,
)

__all__ = [
    "FailureClass",
    "FailureReport",
    "detect_failures",
    "summarize_failures",
]
