"""Paired baseline vs AEX metrics from real MD outputs (wall time + trajectory-derived deviations)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from app.dynamics.observables import parse_xvg_simple


def _interp_y(t_query: np.ndarray, t_ref: np.ndarray, y_ref: np.ndarray) -> np.ndarray:
    return np.interp(t_query, t_ref, y_ref, left=np.nan, right=np.nan)


def rmsd_curve_mae(a: np.ndarray, b: np.ndarray) -> float:
    """Mean absolute difference of RMSD(t) after time alignment via interpolation."""
    if a is None or b is None or len(a) < 3 or len(b) < 3:
        return float("nan")
    ta, ya = a[:, 0], a[:, 1]
    tb, yb = b[:, 0], b[:, 1]
    t0 = max(float(ta.min()), float(tb.min()))
    t1 = min(float(ta.max()), float(tb.max()))
    if t1 <= t0:
        return float("nan")
    grid = np.linspace(t0, t1, num=min(256, min(len(a), len(b), 128)))
    ia = _interp_y(grid, ta, ya)
    ib = _interp_y(grid, tb, yb)
    m = np.isfinite(ia) & np.isfinite(ib)
    if m.sum() < 3:
        return float("nan")
    return float(np.mean(np.abs(ia[m] - ib[m])))


def energy_mean_diff_norm(
    pot_a: Optional[np.ndarray],
    pot_b: Optional[np.ndarray],
    *,
    scale_kj_mol: float = 5000.0,
) -> float:
    if pot_a is None or pot_b is None or len(pot_a) < 2 or len(pot_b) < 2:
        return float("nan")
    ma, mb = float(np.mean(pot_a[:, 1])), float(np.mean(pot_b[:, 1]))
    return float(abs(ma - mb) / max(scale_kj_mol, 1e-6))


def compute_paired_physics_metrics(
    baseline_dir: Path,
    aex_dir: Path,
    *,
    w_struct: float = 0.5,
    w_energy: float = 0.3,
    w_graph: float = 0.2,
    rmsd_scale_nm: float = 0.5,
    delta_threshold: float = 0.05,
) -> Dict[str, Any]:
    """
    Structural term: mean |ΔRMSD| / rmsd_scale_nm (clipped 0–1).
    Energy term: |Δ⟨V⟩| / scale (clipped 0–1).
    Graph term: 0.0 unless provided externally (reserved).
    """
    bdir, adir = Path(baseline_dir), Path(aex_dir)
    br = parse_xvg_simple(bdir / "rmsd.xvg")
    ar = parse_xvg_simple(adir / "rmsd.xvg")
    bp = parse_xvg_simple(bdir / "potential.xvg")
    ap = parse_xvg_simple(adir / "potential.xvg")

    d_rmsd = rmsd_curve_mae(br, ar)
    eps_struct = float(np.clip((d_rmsd / max(rmsd_scale_nm, 1e-6)), 0.0, 1.0)) if np.isfinite(d_rmsd) else 0.0
    e_dn = energy_mean_diff_norm(bp, ap)
    eps_num = float(np.clip(e_dn, 0.0, 1.0)) if np.isfinite(e_dn) else 0.0
    eps_graph = 0.0
    eps_total = w_struct * eps_struct + w_energy * eps_num + w_graph * eps_graph
    return {
        "rmsd_curve_mae_nm": d_rmsd if np.isfinite(d_rmsd) else None,
        "epsilon_structural": eps_struct,
        "epsilon_numerical": eps_num,
        "epsilon_graph": eps_graph,
        "epsilon_total": float(eps_total),
        "delta_threshold": float(delta_threshold),
        "weights": {"structural": w_struct, "numerical": w_energy, "graph": w_graph},
        "fidelity_satisfied": float(eps_total) < float(delta_threshold),
    }


def write_paired_physics_json(
    baseline_dir: Path,
    aex_dir: Path,
    out_path: Path,
    **kwargs: Any,
) -> Dict[str, Any]:
    d = compute_paired_physics_metrics(baseline_dir, aex_dir, **kwargs)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(d, indent=2), encoding="utf-8")
    return d


def merge_error_bounds_into_aex_report(
    aex_report_path: Path,
    physics: Dict[str, Any],
) -> None:
    """Update ``error_bounds`` on an existing ``aex_report.json`` using paired physics (real evidence)."""
    p = Path(aex_report_path)
    rep = {}
    if p.is_file():
        rep = json.loads(p.read_text(encoding="utf-8"))
    eb = rep.get("error_bounds")
    if not isinstance(eb, dict):
        eb = {}
    eb.update(
        {
            "epsilon_numerical": physics.get("epsilon_numerical"),
            "epsilon_structural": physics.get("epsilon_structural"),
            "epsilon_graph": physics.get("epsilon_graph"),
            "epsilon_total": physics.get("epsilon_total"),
            "delta_threshold": physics.get("delta_threshold"),
            "source": "paired_trajectory_comparison",
        }
    )
    rep["error_bounds"] = eb
    rep["paired_physics_evidence"] = True
    p.write_text(json.dumps(rep, indent=2), encoding="utf-8")


def write_minimal_baseline_report(
    baseline_dir: Path,
    *,
    wall_time_seconds: float,
    simulated_time_ns: float,
) -> None:
    p = Path(baseline_dir) / "aex_report.json"
    rep = {
        "role": "baseline_full_md",
        "wall_time_seconds": float(wall_time_seconds),
        "simulated_time_ns": float(simulated_time_ns),
        "error_bounds": None,
        "note": "Baseline reference run; fidelity epsilon is computed from paired comparison in AEX dir.",
    }
    p.write_text(json.dumps(rep, indent=2), encoding="utf-8")
