"""Marginal information gain ΔI from coordinate histogram entropy."""

from __future__ import annotations

from typing import List

import numpy as np


class InformationGainEngine:
    """ΔI = |H(x_t) - H(x_{t-1})|; saturation when ΔI < ε_I."""

    def __init__(self, n_bins: int = 50, eps_info: float = 0.001):
        self.n_bins = n_bins
        self.eps_info = eps_info
        self._entropy_history: List[float] = []

    def update(self, coords: np.ndarray) -> float:
        current_entropy = self._estimate_entropy(coords)
        self._entropy_history.append(current_entropy)
        if len(self._entropy_history) < 2:
            return 1.0
        return abs(self._entropy_history[-1] - self._entropy_history[-2])

    def _estimate_entropy(self, coords: np.ndarray) -> float:
        flat = coords.flatten()[:500]
        if len(flat) == 0:
            return 0.0
        counts, _ = np.histogram(flat, bins=self.n_bins, density=True)
        counts = counts[counts > 0]
        return float(-np.sum(counts * np.log(counts + 1e-10)) / max(len(counts), 1))

    def is_saturated(self, delta_i: float) -> bool:
        return delta_i < self.eps_info
