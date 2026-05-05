"""Compare replicate simulation outputs (distributional)."""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from app.validation.common.constants import DYNAMICS_MIN_REPLICATES_FOR_STATS


def compare_rmsd_replicates(traces: List[Optional[np.ndarray]]) -> Dict[str, float]:
    finals = []
    for tr in traces:
        if tr is not None and len(tr) > 0:
            finals.append(float(tr[-1, 1]))
    if len(finals) < DYNAMICS_MIN_REPLICATES_FOR_STATS:
        return {"n_replicates": float(len(finals)), "rmsd_final_std": float("nan")}
    return {
        "n_replicates": float(len(finals)),
        "rmsd_final_mean": float(np.mean(finals)),
        "rmsd_final_std": float(np.std(finals)),
        "rmsd_final_range": float(np.max(finals) - np.min(finals)),
    }
