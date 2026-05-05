"""GROMACS runner wiring (no binary required for import test)."""

from pathlib import Path

from app.dynamics.gromacs_runner import DynamicsInputs, GROMACSRunner


def test_dynamics_inputs_defaults():
    inp = DynamicsInputs(protein_pdb="/tmp/fake.pdb", job_id="j1", output_dir="/tmp/mdtest")
    assert inp.use_aex is False
    assert inp.dt == 0.002


def test_runner_creates_workdir(tmp_path):
    pdb = tmp_path / "x.pdb"
    pdb.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\n")
    inp = DynamicsInputs(protein_pdb=str(pdb), job_id="job_unit", output_dir=str(tmp_path / "mdroot"))
    r = GROMACSRunner(inp)
    assert r.work_dir.exists()
