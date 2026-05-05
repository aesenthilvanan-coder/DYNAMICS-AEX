"""Lyapunov proxy and spectral (graph Laplacian) stability."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


class LyapunovDetector:
    """Approximate largest Lyapunov exponent from log-separation growth."""

    def __init__(self, window: int = 50, threshold: float = 0.01):
        self.window = window
        self.threshold = threshold
        self._separation_history: List[float] = []

    def update(self, trajectory_divergence: float):
        self._separation_history.append(np.log(max(trajectory_divergence, 1e-10)))
        if len(self._separation_history) > self.window * 2:
            self._separation_history.pop(0)

    def compute_lyapunov(self) -> float:
        if len(self._separation_history) < self.window:
            return 0.0
        recent = np.array(self._separation_history[-self.window :])
        rates = np.diff(recent)
        return float(np.mean(rates))

    def is_chaotic(self) -> bool:
        return self.compute_lyapunov() > self.threshold


class SpectralStabilityChecker:
    """Contact-graph Laplacian eigenvalue drift bound."""

    def __init__(self, contact_cutoff_nm: float = 0.6, n_eigenvalues: int = 10, eps_graph: float = 0.01):
        self.contact_cutoff = contact_cutoff_nm
        self.n_eigenvalues = n_eigenvalues
        self.eps_graph = eps_graph
        self._eigenvalue_history: List[np.ndarray] = []

    def compute_eigenvalues(self, positions: np.ndarray) -> np.ndarray:
        N = len(positions)
        if N < 2:
            return np.zeros(self.n_eigenvalues)
        A = np.zeros((N, N))
        for i in range(N):
            for j in range(i + 1, N):
                dist = np.linalg.norm(positions[i] - positions[j])
                if dist < self.contact_cutoff:
                    A[i, j] = A[j, i] = 1.0
        D = np.diag(A.sum(axis=1))
        L = D - A
        try:
            eigvals = np.linalg.eigvalsh(L)
            eigvals_sorted = np.sort(eigvals)[1 : self.n_eigenvalues + 1]
            if len(eigvals_sorted) < self.n_eigenvalues:
                eigvals_sorted = np.pad(
                    eigvals_sorted, (0, self.n_eigenvalues - len(eigvals_sorted))
                )
            return eigvals_sorted
        except Exception:
            return np.zeros(self.n_eigenvalues)

    def update(self, positions: np.ndarray) -> Tuple[np.ndarray, bool]:
        eigvals = self.compute_eigenvalues(positions)
        self._eigenvalue_history.append(eigvals)
        if len(self._eigenvalue_history) > 20:
            self._eigenvalue_history.pop(0)
        if len(self._eigenvalue_history) < 2:
            return eigvals, True
        prev = self._eigenvalue_history[-2]
        delta = np.linalg.norm(eigvals - prev)
        return eigvals, delta < self.eps_graph
