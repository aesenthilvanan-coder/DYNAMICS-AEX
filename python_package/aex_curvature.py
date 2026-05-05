"""Phase-space curvature field K(t) ≈ d²E/dt² for adaptive timestep bounds."""

from __future__ import annotations

from typing import List, Optional

import numpy as np


class PhaseSpaceCurvature:
    """
    Computes ‖K(t)‖ from energy second-difference over a sliding window.
    Safe timestep multiplier ∝ 1/‖K‖ per spec.
    """

    def __init__(self, window: int = 10):
        self.window = window
        self._energy_buffer: List[float] = []

    def update(self, energy: float, positions: Optional[np.ndarray] = None):
        self._energy_buffer.append(energy)
        if len(self._energy_buffer) > self.window * 3:
            self._energy_buffer.pop(0)

    def compute_curvature_norm(self) -> float:
        if len(self._energy_buffer) < 3:
            return 1.0
        energies = np.array(self._energy_buffer[-self.window :])
        first_diff = np.diff(energies)
        second_diff = np.diff(first_diff)
        curvature = np.sqrt(np.mean(second_diff**2))
        return max(curvature, 1e-6)

    def safe_timestep_multiplier(self) -> float:
        k = self.compute_curvature_norm()
        r_s = 1.0 / k
        return float(np.clip(r_s / 10.0, 0.5, 4.0))
