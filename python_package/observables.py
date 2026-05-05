"""MD observables from GROMACS .xvg (and similar) logs — real traces only."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


def parse_xvg_simple(path: Path) -> Optional[np.ndarray]:
    """Parse two-column GROMACS .xvg (time, value) ignoring comments."""
    if not path.is_file():
        return None
    rows: List[List[float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "@")):
            continue
        parts = s.split()
        if len(parts) >= 2:
            try:
                rows.append([float(parts[0]), float(parts[1])])
            except ValueError:
                continue
    if not rows:
        return None
    return np.array(rows, dtype=np.float64)


def rmsd_stats(time_series: np.ndarray) -> Dict[str, float]:
    """time_series columns [t, rmsd]."""
    if time_series is None or len(time_series) < 2:
        return {"n": 0.0}
    y = time_series[:, 1]
    return {
        "n": float(len(y)),
        "rmsd_mean": float(np.mean(y)),
        "rmsd_std": float(np.std(y)),
        "rmsd_final": float(y[-1]),
        "rmsd_max": float(np.max(y)),
    }


def energy_drift(time_series: np.ndarray) -> Dict[str, float]:
    if time_series is None or len(time_series) < 5:
        return {"n": 0.0}
    y = time_series[:, 1]
    t = time_series[:, 0]
    slope, _ = np.polyfit(t, y, 1)
    return {"n": float(len(y)), "linear_drift_per_ns": float(slope)}


def temperature_stats(time_series: np.ndarray) -> Dict[str, float]:
    """time_series columns [t, T]."""
    if time_series is None or len(time_series) < 2:
        return {"n": 0.0}
    y = time_series[:, 1]
    return {
        "n": float(len(y)),
        "temp_mean": float(np.mean(y)),
        "temp_std": float(np.std(y)),
        "temp_final": float(y[-1]),
    }


def rmsf_stats(time_series: np.ndarray) -> Dict[str, float]:
    """time_series columns [residue_index or time, rmsf] — uses second column as RMSF."""
    if time_series is None or len(time_series) < 2:
        return {"n": 0.0}
    y = time_series[:, 1]
    return {
        "n": float(len(y)),
        "rmsf_mean": float(np.mean(y)),
        "rmsf_max": float(np.max(y)),
    }
