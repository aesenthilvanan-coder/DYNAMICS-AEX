"""AEX engine unit tests."""

import pytest
import numpy as np
from unittest.mock import MagicMock

from app.dynamics.aex_engine import (
    AEXEngine,
    AEXConfig,
    AEXState,
    ExecutionMode,
    PhaseSpaceCurvature,
    InformationGainEngine,
    LyapunovDetector,
    SpectralStabilityChecker,
)


def test_convergence_check_stable_system():
    state = AEXState()
    cfg = AEXConfig(convergence_window=10)
    state.energy_history = [100.0 + 0.01 * i for i in range(20)]
    state.rmsd_history = [0.1 + 0.0001 * i for i in range(20)]
    state.entropy_history = [1.0 - 0.0001 * i for i in range(20)]
    state.graph_eigenvalue_history = [np.array([1.0, 2.0, 3.0]) for _ in range(20)]
    engine = AEXEngine.__new__(AEXEngine)
    engine.state = state
    engine.cfg = cfg
    engine.inputs = MagicMock()
    engine.inputs.dt = 0.002
    assert engine._check_convergence() is True


def test_convergence_not_detected_unstable():
    state = AEXState()
    cfg = AEXConfig(convergence_window=10, eps1_energy_rate=0.5)
    state.energy_history = [100.0 + 10.0 * i for i in range(20)]
    state.rmsd_history = [0.1 for _ in range(20)]
    state.entropy_history = [1.0 for _ in range(20)]
    state.graph_eigenvalue_history = [np.array([1.0, 2.0, 3.0]) for _ in range(20)]
    engine = AEXEngine.__new__(AEXEngine)
    engine.state = state
    engine.cfg = cfg
    engine.inputs = MagicMock()
    assert engine._check_convergence() is False


def test_chaos_detection():
    detector = LyapunovDetector(window=20, threshold=0.01)
    for i in range(25):
        detector.update(1e-8 * np.exp(0.05 * i))
    assert detector.compute_lyapunov() > 0
    assert detector.is_chaotic()


def test_no_chaos_stable():
    detector = LyapunovDetector(window=20, threshold=0.01)
    np.random.seed(0)
    for _ in range(25):
        detector.update(1e-5 + 1e-7 * np.random.randn())
    assert not detector.is_chaotic()


def test_curvature_timestep_scaling():
    curv_low = PhaseSpaceCurvature(window=5)
    curv_high = PhaseSpaceCurvature(window=5)
    for e in [100.0, 100.01, 100.0, 99.99, 100.0]:
        curv_low.update(e)
    for e in [100.0, 120.0, 80.0, 115.0, 85.0]:
        curv_high.update(e)
    dt_low = curv_low.safe_timestep_multiplier()
    dt_high = curv_high.safe_timestep_multiplier()
    assert dt_low >= dt_high


def test_information_saturation():
    engine = InformationGainEngine(n_bins=10, eps_info=0.001)
    coords = np.random.randn(100, 3)
    engine.update(coords)
    for _ in range(10):
        delta = engine.update(coords)
    assert engine.is_saturated(delta)


def test_error_bounds_satisfied():
    state = AEXState()
    state.energy_history = [100.0] * 20
    state.rmsd_history = [0.05] * 20
    state.graph_eigenvalue_history = [np.zeros(10)] * 20
    engine = AEXEngine.__new__(AEXEngine)
    engine.state = state
    engine.cfg = AEXConfig(delta=0.5, w1_numerical=0.3, w2_structural=0.5, w3_topological=0.2)
    engine.inputs = MagicMock()
    engine.inputs.dt = 0.002
    engine.state.current_timestep_multiplier = 1.0
    bounds = engine._compute_error_bounds()
    assert bounds["fidelity_satisfied"]


def test_execution_policy_full_md_on_instability():
    state = AEXState()
    state.local_stable = False
    state.global_stable = True
    state.spectral_stable = True
    state.chaos_detected = False
    engine = AEXEngine.__new__(AEXEngine)
    engine.state = state
    engine.cfg = AEXConfig()
    engine.inputs = MagicMock()
    assert engine._decide_execution_mode() == ExecutionMode.FULL_MD


def test_execution_policy_terminate_on_convergence():
    state = AEXState()
    state.local_stable = True
    state.global_stable = True
    state.spectral_stable = True
    state.chaos_detected = False
    state.energy_history = [100.0 + 0.001 * i for i in range(20)]
    state.rmsd_history = [0.1 + 0.00001 * i for i in range(20)]
    state.entropy_history = [1.0 - 0.0001 * i for i in range(20)]
    state.graph_eigenvalue_history = [np.zeros(10) for _ in range(20)]
    engine = AEXEngine.__new__(AEXEngine)
    engine.state = state
    engine.cfg = AEXConfig(convergence_window=10, eps1_energy_rate=1.0, eps2_rmsd_rate=0.01)
    engine.inputs = MagicMock()
    assert engine._decide_execution_mode() == ExecutionMode.TERMINATE
