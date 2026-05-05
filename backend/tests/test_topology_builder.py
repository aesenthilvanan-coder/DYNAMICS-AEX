"""topology_builder helpers."""

from pathlib import Path

from app.dynamics.topology_builder import merge_ligand_topology, suggest_forcefield_for_pdb, validate_pdb


def test_validate_pdb(tmp_path: Path):
    p = tmp_path / "x.pdb"
    p.write_text("ATOM\n")
    assert validate_pdb(p) is True
    assert validate_pdb(tmp_path / "missing.pdb") is False


def test_suggest_forcefield():
    assert suggest_forcefield_for_pdb("/tmp/x.pdb") == "amber99sb-ildn"


def test_merge_ligand_topology_inserts_include(tmp_path: Path):
    top = tmp_path / "topol.top"
    top.write_text("; Include forcefield parameters\n[ molecules ]\n")
    itp = tmp_path / "ligand.itp"
    itp.write_text("[ moleculetype ]\n")
    merge_ligand_topology(top, itp)
    text = top.read_text()
    assert '#include "ligand.itp"' in text
