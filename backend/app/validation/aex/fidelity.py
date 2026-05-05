"""Fidelity metrics from AEX reports and optional paired baselines."""

from __future__ import annotations

from typing import Any, Dict, Optional


def epsilon_from_report(report: Dict[str, Any]) -> Dict[str, Optional[float]]:
    eb = report.get("error_bounds")
    if not isinstance(eb, dict):
        return {
            "epsilon_total": None,
            "epsilon_numerical": None,
            "epsilon_structural": None,
            "epsilon_graph": None,
        }
    return {
        "epsilon_total": eb.get("epsilon_total"),
        "epsilon_numerical": eb.get("epsilon_numerical"),
        "epsilon_structural": eb.get("epsilon_structural"),
        "epsilon_graph": eb.get("epsilon_graph"),
    }


def fidelity_pass(report: Dict[str, Any], delta: Optional[float] = None) -> bool:
    """
    Strict numerical rule: PASS iff epsilon_total is present and epsilon_total < delta.
    delta = error_bounds.delta_threshold if set, else 1.0 - fidelity_target (default target 0.95).
    No surrogate flags — insufficient numeric evidence => not a pass.
    """
    from app.validation.common.constants import AEX_DEFAULT_FIDELITY_TARGET

    eb = report.get("error_bounds")
    if not isinstance(eb, dict):
        return False
    et = eb.get("epsilon_total")
    if et is None:
        return False
    if delta is None:
        delta = eb.get("delta_threshold")
    if delta is None:
        delta = 1.0 - float(report.get("fidelity_target", AEX_DEFAULT_FIDELITY_TARGET))
    return float(et) < float(delta)
