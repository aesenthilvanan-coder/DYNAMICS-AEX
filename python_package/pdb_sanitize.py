"""PDB fixes before GROMACS pdb2gmx (e.g. incomplete cryo-EM histidine sidechains)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, List, Set, Tuple

_HIS_NAMES = frozenset({"HIS", "HID", "HIE", "HIP"})
_IMIDAZOLE_ATOMS = frozenset({"CG", "ND1", "CD2", "CE1", "NE2"})


def _parse_atom_name(line: str) -> str:
    raw = line[12:16]
    return raw.strip().upper()


def _parse_resname(line: str) -> str:
    return line[17:20].strip().upper()


def _parse_chain_resseq_icode(line: str) -> Tuple[str, str, str]:
    chain = line[21:22] or " "
    resseq = line[22:26].strip()
    icode = line[26:27].strip() or " "
    return chain, resseq, icode


def _set_resname(line: str, new: str) -> str:
    r = new.upper().ljust(3)[:3]
    return line[:17] + r + line[20:]


def _set_atom_name(line: str, new: str) -> str:
    """PDB atom name field cols 13–16 (left-justified per common convention)."""
    a = new.upper().ljust(4)[:4]
    return line[:12] + a + line[16:]


def sanitize_incomplete_histidines_to_ala(pdb_path: Path) -> int:
    """
    Histidine residues without a full imidazole ring (common in truncated models) make
    ``gmx pdb2gmx`` fail. Replace those residues with alanine, keeping only N, CA, C, O, CB.

    Returns the number of residues converted.
    """
    text = pdb_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    recs: List[Tuple[int, str]] = []  # (line_idx, line) for ATOM/HETATM protein-like
    groups: DefaultDict[Tuple[str, str, str], List[int]] = defaultdict(list)

    for i, line in enumerate(lines):
        if not (line.startswith("ATOM  ") or line.startswith("HETATM")):
            continue
        resname = _parse_resname(line)
        if resname not in _HIS_NAMES:
            continue
        chain, resseq, icode = _parse_chain_resseq_icode(line)
        groups[(chain, resseq, icode)].append(i)

    n_converted = 0
    drop_indices: Set[int] = set()

    for key, idxs in groups.items():
        names: Set[str] = set()
        for i in idxs:
            names.add(_parse_atom_name(lines[i]))
        if _IMIDAZOLE_ATOMS.issubset(names):
            continue
        n_converted += 1
        keep = frozenset({"N", "CA", "C", "O", "OXT", "CB"})
        for i in idxs:
            nm = _parse_atom_name(lines[i])
            if nm not in keep:
                drop_indices.add(i)
            else:
                line = lines[i]
                line = _set_resname(line, "ALA")
                if nm == "CB":
                    line = _set_atom_name(line, "CB")
                lines[i] = line

    if not drop_indices and n_converted == 0:
        return 0

    out: List[str] = []
    for i, line in enumerate(lines):
        if i in drop_indices:
            continue
        out.append(line)
    pdb_path.write_text("".join(out), encoding="utf-8")
    return n_converted


def strip_hetatm_records(pdb_path: Path) -> int:
    """
    Remove ``HETATM`` lines (ligands, crystallographic waters). Standard for protein-only
    setup: solvent is added later with ``gmx solvate``.
    """
    text = pdb_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    out = [ln for ln in lines if not ln.startswith("HETATM")]
    n = len(lines) - len(out)
    if n:
        pdb_path.write_text("".join(out), encoding="utf-8")
    return n


def prepare_receptor_pdb_for_gromacs(pdb_path: Path) -> tuple[int, int]:
    """
    Apply all PDB fixes needed for a typical RCSB structure before ``gmx pdb2gmx``.

    Returns ``(n_hetatm_removed, n_histidines_converted_to_ala)``.
    """
    n_het = strip_hetatm_records(pdb_path)
    n_his = sanitize_incomplete_histidines_to_ala(pdb_path)
    return n_het, n_his
