"""AEX fidelity pass rules."""

from app.validation.aex.fidelity import epsilon_from_report, fidelity_pass


def test_fidelity_pass_from_bounds():
    rep = {
        "fidelity_guaranteed": True,
        "error_bounds": {
            "epsilon_total": 0.01,
            "fidelity_satisfied": True,
            "delta_threshold": 0.05,
        },
    }
    assert fidelity_pass(rep) is True
    eps = epsilon_from_report(rep)
    assert eps["epsilon_total"] == 0.01


def test_fidelity_fail_high_epsilon():
    rep = {
        "fidelity_guaranteed": False,
        "fidelity_target": 0.95,
        "error_bounds": {"epsilon_total": 0.5, "fidelity_satisfied": False},
    }
    assert fidelity_pass(rep) is False


def test_fidelity_fail_without_epsilon_total():
    """Strict rule: no numeric epsilon => not a pass (ignore fidelity_satisfied flags)."""
    rep = {
        "fidelity_guaranteed": True,
        "error_bounds": {"fidelity_satisfied": True, "delta_threshold": 0.05},
    }
    assert fidelity_pass(rep) is False
