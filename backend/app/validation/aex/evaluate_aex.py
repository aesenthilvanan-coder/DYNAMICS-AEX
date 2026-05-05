"""Pairwise AEX vs baseline report comparison (real job outputs only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.validation.common.reporting import ensure_output_dir, write_json, write_csv_simple
from app.validation.common.constants import (
    AEX_DEFAULT_FIDELITY_TARGET,
    AEX_MISSING_SPEEDUP,
    AEX_MISSING_WALL_S,
)
from app.validation.aex.fidelity import epsilon_from_report, fidelity_pass
from app.validation.aex.safety import mode_usage_from_log, safety_summary
from app.validation.aex.speed import aggregate_speed
from app.validation.aex.ablations import ablation_manifest


def _delta_from_report(report: Dict[str, Any]) -> float:
    eb = report.get("error_bounds")
    if isinstance(eb, dict) and eb.get("delta_threshold") is not None:
        return float(eb["delta_threshold"])
    return 1.0 - float(report.get("fidelity_target", AEX_DEFAULT_FIDELITY_TARGET))


def _load_report(job_dir: Path) -> Dict[str, Any]:
    p = job_dir / "aex_report.json"
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_paired_physics(aex_dir: Path) -> Optional[Dict[str, Any]]:
    p = aex_dir / "paired_physics_metrics.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _report_is_disallowed_placeholder(rep: Dict[str, Any]) -> bool:
    """Legacy JSON that marked non-empirical QA data — never treated as evidence."""
    if rep.get("synthetic_fixture") is True:
        return True
    return False


def _infer_data_source(
    pair: Dict[str, Any],
    base_rep: Dict[str, Any],
    aex_rep: Dict[str, Any],
    aex_dir: Path,
) -> str:
    if pair.get("data_source"):
        return str(pair["data_source"])
    if _report_is_disallowed_placeholder(base_rep) or _report_is_disallowed_placeholder(aex_rep):
        return "insufficient_evidence"
    if _load_paired_physics(aex_dir) is not None:
        return "real_paired_md"
    eb = aex_rep.get("error_bounds")
    if isinstance(eb, dict) and eb.get("source") == "paired_trajectory_comparison":
        return "real_paired_md"
    if aex_rep.get("paired_physics_evidence"):
        return "real_paired_md"
    if aex_rep.get("wall_time_seconds") is not None and base_rep.get("wall_time_seconds") is not None:
        return "report_only_md"
    return "insufficient_evidence"


def run_aex_validation(
    *,
    pairs_json: Path,
    output_root: Path,
) -> Dict[str, Any]:
    """
    ``pairs_json`` format: { "pairs": [ {"id": "...", "baseline_dir": "...", "aex_dir": "...", ...} ] }

    Expects real job directories. Reports with ``synthetic_fixture: true`` are ignored for evidence
    (classified as ``insufficient_evidence``).
    """
    out = ensure_output_dir(output_root, "aex")
    plots = ensure_output_dir(out, "plots")
    if not pairs_json.is_file():
        pairs_json.parent.mkdir(parents=True, exist_ok=True)
        pairs_json.write_text(
            json.dumps(
                {
                    "pairs": [],
                    "_comment": "Add real paired runs; use run_aex_paired_benchmark.py.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    spec = json.loads(pairs_json.read_text(encoding="utf-8"))
    pairs = spec.get("pairs", [])
    speed_rows: List[Dict[str, Any]] = []
    fidelity_rows: List[Dict[str, Any]] = []
    mode_rows: List[Dict[str, Any]] = []
    rollback_rows: List[Dict[str, Any]] = []

    for pair in pairs:
        pid = pair.get("id", "pair")
        bdir = Path(pair.get("baseline_dir", ""))
        adir = Path(pair.get("aex_dir", ""))
        base_rep = _load_report(bdir)
        aex_rep = _load_report(adir)
        physics = _load_paired_physics(adir)

        data_source = _infer_data_source(pair, base_rep, aex_rep, adir)

        base_wall = base_rep.get("wall_time_seconds")
        aex_wall = aex_rep.get("wall_time_seconds")
        speedup_meas: Optional[float] = None
        if base_wall is not None and aex_wall is not None and float(aex_wall) > 0:
            speedup_meas = float(base_wall) / float(aex_wall)

        speed_rows.append(
            {
                "pair_id": pid,
                "data_source": data_source,
                "baseline_wall_s": base_wall,
                "aex_wall_s": aex_wall,
                "speedup_measured": speedup_meas,
                "reported_speedup": aex_rep.get("speedup"),
            }
        )

        eps = epsilon_from_report(aex_rep)
        if physics is not None:
            eps = {
                "epsilon_total": physics.get("epsilon_total"),
                "epsilon_numerical": physics.get("epsilon_numerical"),
                "epsilon_structural": physics.get("epsilon_structural"),
                "epsilon_graph": physics.get("epsilon_graph"),
            }
        delta_applied = (
            physics.get("delta_threshold") if physics and physics.get("delta_threshold") is not None else None
        )
        if delta_applied is None:
            delta_applied = _delta_from_report(aex_rep)

        merged_for_pass = dict(aex_rep)
        if physics is not None:
            merged_for_pass = {
                **aex_rep,
                "error_bounds": {
                    **(aex_rep.get("error_bounds") or {}),
                    "epsilon_total": physics.get("epsilon_total"),
                    "epsilon_numerical": physics.get("epsilon_numerical"),
                    "epsilon_structural": physics.get("epsilon_structural"),
                    "epsilon_graph": physics.get("epsilon_graph"),
                    "delta_threshold": physics.get("delta_threshold", delta_applied),
                },
            }

        if data_source == "insufficient_evidence":
            fpass = False
        else:
            fpass = fidelity_pass(merged_for_pass, delta=delta_applied if physics else None)

        fidelity_rows.append(
            {
                "pair_id": pid,
                "data_source": data_source,
                **eps,
                "delta_applied": float(delta_applied) if delta_applied is not None else None,
                "fidelity_pass": fpass,
                "fidelity_guaranteed_flag": aex_rep.get("fidelity_guaranteed"),
            }
        )
        elog = aex_rep.get("execution_log") or []
        mode_rows.append({"pair_id": pid, **mode_usage_from_log(elog)})
        rollback_rows.append({"pair_id": pid, **safety_summary(aex_rep)})

    write_csv_simple(out / "speedup_table.csv", speed_rows)
    write_csv_simple(out / "fidelity_table.csv", fidelity_rows)
    write_csv_simple(out / "aex_mode_usage.csv", mode_rows)
    write_csv_simple(out / "rollback_events.csv", rollback_rows)
    write_json(out / "ablation_protocol.json", ablation_manifest())

    n_real = sum(1 for r in fidelity_rows if r.get("data_source") == "real_paired_md")
    n_insufficient = sum(1 for r in fidelity_rows if r.get("data_source") == "insufficient_evidence")

    summary = {
        "version": 3,
        "n_pairs": len(pairs),
        "data_source": "mixed" if pairs else "empty",
        "n_real_paired_md_pairs": n_real,
        "n_insufficient_evidence_pairs": n_insufficient,
        "speed": aggregate_speed(
            [
                {
                    "speedup": r.get("speedup_measured")
                    if r.get("speedup_measured") is not None
                    else r.get("reported_speedup", AEX_MISSING_SPEEDUP),
                    "wall_time_seconds": r.get("aex_wall_s", AEX_MISSING_WALL_S),
                }
                for r in speed_rows
            ]
        ),
        "fidelity_pass_rate": sum(1 for r in fidelity_rows if r.get("fidelity_pass"))
        / max(len(fidelity_rows), 1),
        "epsilon_total_by_pair": [r.get("epsilon_total") for r in fidelity_rows],
        "fidelity_rule": "pass iff epsilon_total is not None and epsilon_total < delta_applied "
        "(paired physics preferred); placeholder reports never pass",
        "delta_definition": "delta from paired physics or error_bounds.delta_threshold or 1.0 - fidelity_target",
        "plots_dir": str(plots),
        "note": "Real paired MD only; legacy synthetic_fixture reports are not counted as evidence.",
    }
    write_json(out / "aex_benchmark_summary.json", summary)

    report_md = out / "aex_validation_report.md"
    lines = [
        "# AEX validation report",
        "",
        "## Evidence",
        f"- **Pairs evaluated**: {len(pairs)}",
        f"- **Real paired MD (trajectory-derived ε)**: {n_real}",
        f"- **Insufficient evidence (missing or disallowed reports)**: {n_insufficient}",
        f"- **Fidelity pass rate (strict ε rule)**: {summary['fidelity_pass_rate']}",
        "",
        "## Engineering vs science",
        "- **Engineering pass**: jobs completed, reports parseable, tables written.",
        "- **Scientific evidence strength**: high only when `data_source=real_paired_md` and ε is from paired outputs.",
        "",
        "## Limitations",
        "- Short simulations and coarse ε definitions bound what can be claimed on a poster.",
        "",
    ]
    report_md.write_text("\n".join(lines), encoding="utf-8")

    return summary
