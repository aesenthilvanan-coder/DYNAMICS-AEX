"""MD failure taxonomy (ligand escape, energy blow-up, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

from app.validation.common.constants import (
    DYNAMICS_ENERGY_JUMP_MAX,
    DYNAMICS_LIGAND_ESCAPE_FRAC_OF_MAX,
    DYNAMICS_LIGAND_ESCAPE_MIN_LAST,
    DYNAMICS_RMSD_SPIKE_MAX,
    DYNAMICS_TEMP_STD_MAX,
)


class FailureClass(str, Enum):
    LIGAND_ESCAPE = "ligand_escape"
    ENERGY_EXPLOSION = "energy_explosion"
    TEMPERATURE_UNSTABLE = "temperature_unstable"
    PRESSURE_UNSTABLE = "pressure_unstable"
    RMSD_SPIKE = "rmsd_spike"
    REPLICATE_DIVERGENCE = "replicate_divergence"
    NO_OUTPUT = "no_output"
    NONE = "none"


@dataclass
class FailureReport:
    system_id: str
    failure_class: FailureClass
    detail: str
    metrics: Dict[str, Any]


def detect_failures(
    system_id: str,
    *,
    rmsd_trace: Optional[np.ndarray],
    energy_trace: Optional[np.ndarray],
    temp_trace: Optional[np.ndarray],
) -> FailureReport:
    """Rule-based flags (conservative)."""
    if rmsd_trace is None and energy_trace is None and temp_trace is None:
        return FailureReport(system_id, FailureClass.NO_OUTPUT, "Missing traces", {})

    metrics: Dict[str, Any] = {}
    if rmsd_trace is not None and len(rmsd_trace) > 5:
        y = rmsd_trace[:, 1]
        metrics["rmsd_max"] = float(np.max(y))
        if np.max(y) > DYNAMICS_RMSD_SPIKE_MAX:
            return FailureReport(
                system_id,
                FailureClass.RMSD_SPIKE,
                f"RMSD max > {DYNAMICS_RMSD_SPIKE_MAX}",
                metrics,
            )
        if y[-1] > DYNAMICS_LIGAND_ESCAPE_FRAC_OF_MAX * np.max(y) and y[-1] > DYNAMICS_LIGAND_ESCAPE_MIN_LAST:
            return FailureReport(
                system_id,
                FailureClass.LIGAND_ESCAPE,
                "Terminal RMSD > 0.8*max and > 2.0",
                metrics,
            )
    if energy_trace is not None and len(energy_trace) > 5:
        y = energy_trace[:, 1]
        metrics["energy_range"] = float(np.max(y) - np.min(y))
        if np.max(np.abs(np.diff(y))) > DYNAMICS_ENERGY_JUMP_MAX:
            return FailureReport(
                system_id,
                FailureClass.ENERGY_EXPLOSION,
                f"|Δenergy| max > {DYNAMICS_ENERGY_JUMP_MAX:g}",
                metrics,
            )
    if temp_trace is not None and len(temp_trace) > 5:
        y = temp_trace[:, 1]
        metrics["temp_std"] = float(np.std(y))
        if np.std(y) > DYNAMICS_TEMP_STD_MAX:
            return FailureReport(
                system_id,
                FailureClass.TEMPERATURE_UNSTABLE,
                f"Temperature std > {DYNAMICS_TEMP_STD_MAX} K",
                metrics,
            )
    return FailureReport(system_id, FailureClass.NONE, "No failure rule triggered", metrics)


def summarize_failures(reports: List[FailureReport]) -> List[Dict[str, Any]]:
    return [
        {
            "system_id": r.system_id,
            "failure_class": r.failure_class.value,
            "detail": r.detail,
            "metrics": r.metrics,
        }
        for r in reports
    ]
