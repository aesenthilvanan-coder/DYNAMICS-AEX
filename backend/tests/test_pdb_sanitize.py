"""PDB preprocessing for GROMACS."""

from pathlib import Path

from app.dynamics.pdb_sanitize import (
    prepare_receptor_pdb_for_gromacs,
    sanitize_incomplete_histidines_to_ala,
    strip_hetatm_records,
)


def test_strip_hetatm(tmp_path: Path):
    p = tmp_path / "x.pdb"
    p.write_text(
        "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\n"
        "HETATM    2  O   HOH A   2       1.000   0.000   0.000  1.00  0.00           O\n",
        encoding="utf-8",
    )
    assert strip_hetatm_records(p) == 1
    assert "HETATM" not in p.read_text()


def test_incomplete_his_to_ala(tmp_path: Path):
    p = tmp_path / "x.pdb"
    p.write_text(
        "ATOM      1  N   HIS A 398      25.537   4.278 -16.959  1.00  0.00           N\n"
        "ATOM      2  CA  HIS A 398      26.930   3.846 -17.033  1.00  0.00           C\n"
        "ATOM      3  C   HIS A 398      27.250   3.199 -18.376  1.00  0.00           C\n"
        "ATOM      4  O   HIS A 398      28.121   3.674 -19.114  1.00  0.00           O\n"
        "ATOM      5  CB  HIS A 398      27.240   2.881 -15.886  1.00  0.00           C\n",
        encoding="utf-8",
    )
    assert sanitize_incomplete_histidines_to_ala(p) == 1
    body = p.read_text()
    assert "HIS" not in body
    assert "ALA" in body


def test_prepare_combined_order(tmp_path: Path):
    p = tmp_path / "x.pdb"
    p.write_text(
        "ATOM      1  N   HIS A 398      25.537   4.278 -16.959  1.00  0.00           N\n"
        "ATOM      2  CA  HIS A 398      26.930   3.846 -17.033  1.00  0.00           C\n"
        "ATOM      3  C   HIS A 398      27.250   3.199 -18.376  1.00  0.00           C\n"
        "ATOM      4  O   HIS A 398      28.121   3.674 -19.114  1.00  0.00           O\n"
        "ATOM      5  CB  HIS A 398      27.240   2.881 -15.886  1.00  0.00           C\n"
        "HETATM    9  O   HOH A 399       0.000   0.000   0.000  1.00  0.00           O\n",
        encoding="utf-8",
    )
    nh, nc = prepare_receptor_pdb_for_gromacs(p)
    assert nh == 1
    assert nc == 1
