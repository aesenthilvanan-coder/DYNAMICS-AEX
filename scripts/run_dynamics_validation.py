#!/usr/bin/env python3
"""DYNAMICS (GROMACS) validation from benchmark manifest — real .xvg / extraction only."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

from app.validation.dynamics.evaluate_dynamics import run_dynamics_validation  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--benchmark-json",
        type=Path,
        default=ROOT / "data" / "validation" / "dynamics_benchmarks.json",
    )
    ap.add_argument("--output-root", type=Path, default=ROOT / "outputs" / "validation")
    ap.add_argument(
        "--no-auto-extract",
        action="store_true",
        help="Do not run gmx rms/energy to build .xvg from job_dir outputs.",
    )
    ap.add_argument("--gmx-bin", type=str, default="", help="Override GROMACS binary for extraction")
    args = ap.parse_args()
    run_dynamics_validation(
        benchmark_json=args.benchmark_json,
        output_root=args.output_root.resolve(),
        auto_extract_from_job_dir=not args.no_auto_extract,
        gmx_bin=args.gmx_bin or None,
    )
    print(f"Wrote DYNAMICS validation under {args.output_root.resolve() / 'dynamics'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
