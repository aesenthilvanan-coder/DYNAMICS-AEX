"""Speed metrics from AEX reports."""

from __future__ import annotations

from typing import Any, Dict, List

from app.validation.common.constants import AEX_MISSING_SPEEDUP, AEX_MISSING_WALL_S


def _speed_field(row: Dict[str, Any], key: str, default: float) -> float:
    v = row.get(key, default)
    if v is None:
        return float(default)
    return float(v)


def aggregate_speed(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    if not rows:
        return {
            "n": 0.0,
            "speedup_mean": None,
            "speedup_median": None,
            "wall_time_mean": None,
        }
    sp = [_speed_field(r, "speedup", AEX_MISSING_SPEEDUP) for r in rows]
    wall = [_speed_field(r, "wall_time_seconds", AEX_MISSING_WALL_S) for r in rows]
    return {
        "n": float(len(rows)),
        "speedup_mean": float(sum(sp) / len(sp)),
        "speedup_median": float(sorted(sp)[len(sp) // 2]),
        "wall_time_mean": float(sum(wall) / len(wall)) if wall else 0.0,
    }
