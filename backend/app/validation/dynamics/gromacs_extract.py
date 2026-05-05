"""Compatibility re-exports; canonical implementation is ``app.dynamics.gromacs_extract``."""

from app.dynamics.gromacs_extract import (
    ensure_observables_for_job_dir,
    extract_energy_xvgs,
    extract_rmsd_xvg,
    extract_rmsf_xvg,
)

__all__ = [
    "ensure_observables_for_job_dir",
    "extract_energy_xvgs",
    "extract_rmsd_xvg",
    "extract_rmsf_xvg",
]
