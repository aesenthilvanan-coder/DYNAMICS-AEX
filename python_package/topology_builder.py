"""Topology + forcefield helpers (extend for ligand CGenFF/GAFF pipelines)."""

from pathlib import Path
from typing import Optional


def validate_pdb(path: str | Path) -> bool:
    p = Path(path)
    return p.exists() and p.suffix.lower() in (".pdb", ".ent")


def suggest_forcefield_for_pdb(_path: str | Path) -> str:
    return "amber99sb-ildn"


def merge_ligand_topology(
    main_top: Path,
    ligand_itp: Path,
    posre_include: Optional[str] = None,
) -> None:
    """Append ligand include to topol.top if missing."""
    text = main_top.read_text()
    inc = '#include "ligand.itp"'
    if inc not in text:
        needle = "; Include forcefield parameters"
        if needle in text:
            text = text.replace(needle, needle + "\n" + inc)
        else:
            text = inc + "\n" + text
        main_top.write_text(text)
