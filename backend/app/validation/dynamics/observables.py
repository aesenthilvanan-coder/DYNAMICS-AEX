"""Compatibility re-exports; canonical implementation is ``app.dynamics.observables``."""

from app.dynamics.observables import (
    energy_drift,
    parse_xvg_simple,
    rmsd_stats,
    rmsf_stats,
    temperature_stats,
)

__all__ = [
    "energy_drift",
    "parse_xvg_simple",
    "rmsd_stats",
    "rmsf_stats",
    "temperature_stats",
]
