#!/usr/bin/env python3
"""
Run a **real** paired baseline MD vs AEX MD (short production) and write trajectory-derived ε + timing.

Requires GROMACS on PATH. This is a minimal engineering benchmark, not converged sampling.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

from app.dynamics.gromacs_runner import DynamicsInputs, GROMACSRunner  # noqa: E402
from app.validation.aex.paired_md import (  # noqa: E402
    compute_paired_physics_metrics,
    merge_error_bounds_into_aex_report,
    write_minimal_baseline_report,
)
from app.validation.dynamics.gromacs_extract import ensure_observables_for_job_dir  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--receptor-pdb",
        type=Path,
        required=True,
        help="Input protein PDB (e.g. data/test_systems/d2r_ligand/receptor.pdb)",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "md_paired_aex",
    )
    ap.add_argument("--pair-id", type=str, default="paired_md_1")
    ap.add_argument("--production-steps", type=int, default=8000, help="Short run; ~16 ps at dt=0.002")
    ap.add_argument("--delta", type=float, default=0.05)
    args = ap.parse_args()

    gmx = shutil.which("gmx") or shutil.which("gmx_mpi")
    if not gmx:
        logging.error("GROMACS (gmx) not found on PATH; cannot run paired benchmark.")
        return 1

    pdb = args.receptor_pdb.resolve()
    if not pdb.is_file():
        logging.error("Missing receptor PDB: %s", pdb)
        return 1

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    common = dict(
        protein_pdb=str(pdb),
        output_dir=str(out),
        production_steps=args.production_steps,
        em_steps=8000,
        nvt_steps=25000,
        npt_steps=25000,
        dt=0.002,
    )

    logging.info("Running baseline MD...")
    base_in = DynamicsInputs(job_id="baseline_md", use_aex=False, **common)
    rb = GROMACSRunner(base_in).run()
    if not rb.success:
        logging.error("Baseline MD failed: %s", rb.error_message)
        return 1
    bdir = Path(rb.output_dir)
    ensure_observables_for_job_dir(bdir, gmx_bin=gmx, extract=True)
    write_minimal_baseline_report(
        bdir,
        wall_time_seconds=rb.wall_time_seconds,
        simulated_time_ns=rb.simulated_time_ns,
    )

    logging.info("Running AEX MD...")
    aex_in = DynamicsInputs(job_id="aex_md", use_aex=True, **common)
    ra = GROMACSRunner(aex_in).run()
    if not ra.success:
        logging.error("AEX MD failed: %s", ra.error_message)
        return 1
    adir = Path(ra.output_dir)
    ensure_observables_for_job_dir(adir, gmx_bin=gmx, extract=True)

    phys = compute_paired_physics_metrics(bdir, adir, delta_threshold=args.delta)
    phys["baseline_wall_s"] = rb.wall_time_seconds
    phys["aex_wall_s"] = ra.wall_time_seconds
    if ra.wall_time_seconds and ra.wall_time_seconds > 0:
        phys["speedup_wall"] = rb.wall_time_seconds / ra.wall_time_seconds
    paired_path = adir / "paired_physics_metrics.json"
    paired_path.write_text(json.dumps(phys, indent=2), encoding="utf-8")

    aex_rep_file = adir / "aex_report.json"
    if aex_rep_file.is_file():
        merge_error_bounds_into_aex_report(aex_rep_file, phys)
    else:
        rep = {
            "wall_time_seconds": ra.wall_time_seconds,
            "simulated_time_ns": ra.simulated_time_ns,
            "speedup": phys.get("speedup_wall"),
            "fidelity_target": 0.95,
            "error_bounds": {
                "epsilon_numerical": phys.get("epsilon_numerical"),
                "epsilon_structural": phys.get("epsilon_structural"),
                "epsilon_graph": phys.get("epsilon_graph"),
                "epsilon_total": phys.get("epsilon_total"),
                "delta_threshold": phys.get("delta_threshold"),
                "source": "paired_trajectory_comparison",
            },
            "paired_physics_evidence": True,
        }
        aex_rep_file.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    pairs_out = out / "aex_pairs_fragment.json"
    fragment = {
        "pairs": [
            {
                "id": args.pair_id,
                "baseline_dir": str(bdir.resolve()),
                "aex_dir": str(adir.resolve()),
                "data_source": "real_paired_md",
            }
        ]
    }
    pairs_out.write_text(json.dumps(fragment, indent=2), encoding="utf-8")
    logging.info("Wrote %s — merge into data/validation/aex_pairs.json for validation.", pairs_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
