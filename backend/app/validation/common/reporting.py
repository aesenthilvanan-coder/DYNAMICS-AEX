"""Report directories and markdown assembly."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def ensure_output_dir(root: Path, *sub: str) -> Path:
    p = root.joinpath(*sub)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def append_final_report(
    path: Path,
    *,
    section_title: str,
    body_md: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    block = f"\n\n## {section_title}\n\n*Generated (UTC): {ts}*\n\n{body_md}\n"
    if path.is_file():
        path.write_text(path.read_text(encoding="utf-8") + block, encoding="utf-8")
    else:
        path.write_text(
            f"# CALY360 — Final validation report\n\n{block}",
            encoding="utf-8",
        )


def write_csv_simple(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        if fieldnames:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                w.writeheader()
        else:
            path.write_text("", encoding="utf-8")
        return
    if fieldnames is None:
        fieldnames = sorted({k for r in rows for k in r.keys()})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
