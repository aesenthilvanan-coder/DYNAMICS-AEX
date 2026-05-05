#!/usr/bin/env python3
"""AEX speed/fidelity validation from paired job directories."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

from app.validation.aex.evaluate_aex import run_aex_validation  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pairs-json",
        type=Path,
        default=ROOT / "data" / "validation" / "aex_pairs.json",
    )
    ap.add_argument("--output-root", type=Path, default=ROOT / "outputs" / "validation")
    args = ap.parse_args()
    run_aex_validation(pairs_json=args.pairs_json, output_root=args.output_root.resolve())
    print(f"Wrote AEX validation under {args.output_root.resolve() / 'aex'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
