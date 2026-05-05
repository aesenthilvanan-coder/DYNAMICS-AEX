"""Safety / rollback statistics from AEX execution logs."""

from __future__ import annotations

from typing import Any, Dict, List


def safety_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rollback_count": int(report.get("rollback_count", 0)),
        "chaos_events": int(report.get("chaos_events", 0)),
        "early_terminated": bool(report.get("early_terminated", False)),
        "segments_run": int(report.get("segments_run", 0)),
        "segments_skipped": int(report.get("segments_skipped", 0)),
    }


def mode_usage_from_log(execution_log: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for step in execution_log:
        mode = step.get("mode", "unknown")
        counts[mode] = counts.get(mode, 0) + 1
    return counts
