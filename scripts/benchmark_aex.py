"""Summarize AEX reports from completed DYNAMICS job directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_reports(root: Path) -> list[tuple[str, dict]]:
    rows: list[tuple[str, dict]] = []
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        rep = p / "aex_report.json"
        if rep.is_file():
            with open(rep, encoding="utf-8") as f:
                rows.append((p.name, json.load(f)))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Aggregate aex_report.json files under a parent directory.")
    parser.add_argument(
        "--md-root",
        type=Path,
        default=Path("/tmp/caly360_md"),
        help="Parent of per-job folders containing aex_report.json",
    )
    args = parser.parse_args()
    if not args.md_root.is_dir():
        print(f"No directory: {args.md_root}", file=sys.stderr)
        sys.exit(1)

    reports = load_reports(args.md_root)
    if not reports:
        print(f"No aex_report.json under {args.md_root}")
        sys.exit(0)

    print(f"{'job_id':<40} {'speedup':>8} {'fidelity_ok':>12} {'steps_skip':>10} {'wall_s':>8}")
    for jid, r in reports:
        print(
            f"{jid:<40} "
            f"{r.get('speedup', 0):>8.2f} "
            f"{str(r.get('fidelity_guaranteed', '')):>12} "
            f"{r.get('steps_skipped', 0):>10} "
            f"{r.get('wall_time_seconds', 0):>8.1f}"
        )


if __name__ == "__main__":
    main()
