"""Bootstrap confidence intervals for scalar metrics."""

from __future__ import annotations

import math
from typing import Callable, Optional, Tuple

import numpy as np


def bootstrap_ci(
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    y_true: np.ndarray,
    y_score: np.ndarray,
    *,
    n_boot: int = 1000,
    seed: int = 42,
    confidence: float = 0.95,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Returns (point_estimate, ci_low, ci_high). metric_fn(y_true_sample, y_score_sample) -> float.
    """
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    n = len(y_true)
    if n < 5:
        try:
            pe = float(metric_fn(y_true, y_score))
        except Exception:
            pe = float("nan")
        return pe, None, None
    try:
        point = float(metric_fn(y_true, y_score))
    except Exception:
        return None, None, None
    stats: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        try:
            v = float(metric_fn(y_true[idx], y_score[idx]))
        except Exception:
            continue
        if math.isfinite(v):
            stats.append(v)
    if len(stats) < n_boot // 10:
        return point, None, None
    alpha = (1 - confidence) / 2
    lo, hi = np.quantile(stats, [alpha, 1 - alpha])
    return point, float(lo), float(hi)
