"""AEX ablation protocol placeholders (requires re-run with toggles in AEXConfig)."""

from __future__ import annotations

ABLATION_MATRIX = [
    {"id": "no_chaos_fallback", "description": "Disable chaos → FULL_MD escalation in engine config."},
    {"id": "no_spectral_check", "description": "Relax spectral stability gate (eps3 → inf)."},
    {"id": "no_convergence_stop", "description": "Disable early TERMINATE on convergence."},
    {"id": "no_rollback", "description": "Disable segment rollback on failure."},
    {"id": "relaxed_delta", "description": "Increase fidelity delta (weaker epsilon bound)."},
]


def ablation_manifest() -> dict:
    return {"ablations": ABLATION_MATRIX, "note": "Implement by cloning AEXConfig in benchmark driver."}
