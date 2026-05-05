"""Orchestrate DYNAMICS validation from a benchmark JSON manifest."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.validation.common.reporting import ensure_output_dir, write_json, write_csv_simple

from .failures import FailureReport, detect_failures, summarize_failures
from .gromacs_extract import ensure_observables_for_job_dir
from .observables import (
    energy_drift,
    parse_xvg_simple,
    rmsd_stats,
    rmsf_stats,
    temperature_stats,
)
from .reproducibility import compare_rmsd_replicates


def run_dynamics_validation(
    *,
    benchmark_json: Path,
    output_root: Path,
    auto_extract_from_job_dir: bool = True,
    gmx_bin: Optional[str] = None,
) -> Dict[str, Any]:
    """
    ``benchmark_json`` rows: {id, job_dir?, rmsd_xvg?, energy_xvg?, temp_xvg?, rmsf_xvg?, replicate_of?}

    Uses **only** real `.xvg` data (from paths or extracted from ``job_dir`` via GROMACS when enabled).
    Missing traces are reported as ``data_source: missing`` — no fabricated trajectories.
    """
    from app.config import settings

    gmx = (gmx_bin or "").strip() or settings.gromacs_executable()

    out = ensure_output_dir(output_root, "dynamics")
    plots = ensure_output_dir(out, "plots")
    if not benchmark_json.is_file():
        payload = {
            "version": 1,
            "systems": [],
            "_comment": "Add systems with job_dir (md.tpr/md.xtc/md.edr) or explicit rmsd_xvg paths after MD.",
        }
        benchmark_json.parent.mkdir(parents=True, exist_ok=True)
        benchmark_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    spec = json.loads(benchmark_json.read_text(encoding="utf-8"))
    systems: List[Dict[str, Any]] = spec.get("systems", [])
    rows: List[Dict[str, Any]] = []
    failures: List[FailureReport] = []
    replicate_groups: Dict[str, List] = {}

    n_real = 0
    n_missing = 0

    for sys in systems:
        sys_row = dict(sys)
        sid = sys_row.get("id", "unknown")
        job = Path(sys_row["job_dir"]) if sys_row.get("job_dir") else None
        rmsd_path = Path(sys_row["rmsd_xvg"]) if sys_row.get("rmsd_xvg") else None
        if job and job.is_dir() and not (rmsd_path and rmsd_path.is_file()) and auto_extract_from_job_dir:
            try:
                extracted = ensure_observables_for_job_dir(job, gmx_bin=gmx, extract=True)
                if extracted.get("rmsd_xvg"):
                    rmsd_path = Path(extracted["rmsd_xvg"])
                if not sys_row.get("energy_xvg") and extracted.get("energy_xvg"):
                    sys_row["energy_xvg"] = extracted["energy_xvg"]
                if not sys_row.get("temp_xvg") and extracted.get("temp_xvg"):
                    sys_row["temp_xvg"] = extracted["temp_xvg"]
                if not sys_row.get("rmsf_xvg") and extracted.get("rmsf_xvg"):
                    sys_row["rmsf_xvg"] = extracted["rmsf_xvg"]
            except Exception:
                pass
        if job and not rmsd_path:
            cand = job / "rmsd.xvg"
            rmsd_path = cand if cand.is_file() else rmsd_path

        en_path = Path(sys_row["energy_xvg"]) if sys_row.get("energy_xvg") else None
        tp_path = Path(sys_row["temp_xvg"]) if sys_row.get("temp_xvg") else None
        rmsf_path = Path(sys_row["rmsf_xvg"]) if sys_row.get("rmsf_xvg") else None

        data_source = "missing"
        rmsd = parse_xvg_simple(rmsd_path) if rmsd_path and rmsd_path.is_file() else None
        if rmsd is not None:
            data_source = "real_md"
            n_real += 1
        else:
            n_missing += 1

        energy = parse_xvg_simple(en_path) if en_path and en_path.is_file() else None
        temp = parse_xvg_simple(tp_path) if tp_path and tp_path.is_file() else None
        rmsf = parse_xvg_simple(rmsf_path) if rmsf_path and rmsf_path.is_file() else None

        rs = rmsd_stats(rmsd) if rmsd is not None else {"n": 0}
        ed = energy_drift(energy) if energy is not None else {}
        ts = temperature_stats(temp) if temp is not None else {}
        rf = rmsf_stats(rmsf) if rmsf is not None else {}
        sim_ns = sys_row.get("simulated_time_ns")
        row = {
            "system_id": sid,
            "data_source": data_source,
            "simulated_time_ns": sim_ns,
            **rs,
            **ed,
            **ts,
            **rf,
        }
        rows.append(row)

        fr = detect_failures(sid, rmsd_trace=rmsd, energy_trace=energy, temp_trace=temp)
        failures.append(fr)

        rep_key = sys.get("replicate_group") or sid
        replicate_groups.setdefault(rep_key, []).append(rmsd)

    write_csv_simple(out / "benchmark_systems.csv", rows)
    write_csv_simple(out / "failure_summary.csv", summarize_failures(failures))

    rep_stats: List[Dict[str, Any]] = []
    for gid, trs in replicate_groups.items():
        rep_stats.append({"group_id": gid, **compare_rmsd_replicates(trs)})
    write_csv_simple(out / "replicate_statistics.csv", rep_stats)

    fail_classes = Counter(f.failure_class.value for f in failures)

    summary = {
        "version": 3,
        "n_systems": len(systems),
        "n_failures": sum(1 for f in failures if f.failure_class.value != "none"),
        "data_source": "real_md" if n_real == len(systems) and systems else ("mixed" if n_real else "none"),
        "n_real_md_systems": n_real,
        "n_missing_traces": n_missing,
        "auto_extract_from_job_dir": auto_extract_from_job_dir,
        "failures_by_class": dict(fail_classes),
        "plots_dir": str(plots),
        "note": "No synthetic trajectories: systems without RMSD .xvg count as missing.",
    }
    write_json(out / "dynamics_validation_summary.json", summary)

    report_md = out / "dynamics_validation_report.md"
    lines = [
        "# DYNAMICS validation report",
        "",
        "## Data sources",
        f"- **Real MD-backed systems (RMSD trace)**: {n_real}",
        f"- **Missing / no RMSD**: {n_missing}",
        "",
        "## Failures",
        f"- **Total systems**: {len(systems)}",
        f"- **Failure flags (non-none)**: {summary['n_failures']}",
        f"- **By class**: {dict(fail_classes)}",
        "",
        "## Interpretation",
        "- Thresholds are heuristic stability checks, not proof of sampling quality.",
        "- Very short production runs are **engineering smoke tests** for the GROMACS pipeline, not publications-grade kinetics.",
        "",
    ]
    report_md.write_text("\n".join(lines), encoding="utf-8")

    return summary
