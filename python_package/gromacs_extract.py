"""Extract observable .xvg files from a completed GROMACS job directory (real compute)."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional override: e.g. export CALY360_GMX_RMS_STDIN=$'5\n5\n'  (fit group + RMSD group)
_RMS_ENV = "CALY360_GMX_RMS_STDIN"
_RMSF_ENV = "CALY360_GMX_RMSF_STDIN"


def _run_gmx(
    gmx_bin: str,
    cwd: Path,
    args: list,
    *,
    stdin: Optional[str] = None,
) -> subprocess.CompletedProcess:
    cmd = [gmx_bin] + args
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        input=stdin,
        capture_output=True,
        text=True,
        timeout=600,
    )


def _xvg_has_numeric_rows(path: Path, min_rows: int = 3) -> bool:
    if not path.is_file() or path.stat().st_size < 20:
        return False
    n = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "@")):
            continue
        parts = s.split()
        if len(parts) >= 2:
            try:
                float(parts[0])
                float(parts[1])
                n += 1
            except ValueError:
                continue
        if n >= min_rows:
            return True
    return False


def extract_rmsd_xvg(
    job_dir: Path,
    *,
    gmx_bin: str = "gmx",
    tpr_name: str = "md.tpr",
    xtc_name: str = "md.xtc",
    out_name: str = "rmsd.xvg",
) -> Optional[Path]:
    """
    Fit + RMSD groups for ``gmx rms``. Tries several common index orders (pdb2gmx / force-field
    dependent), then optional env ``CALY360_GMX_RMS_STDIN`` (exact stdin, e.g. ``5\\n5\\n``).
    """
    tpr = job_dir / tpr_name
    xtc = job_dir / xtc_name
    out = job_dir / out_name
    if not tpr.is_file() or not xtc.is_file():
        return None
    if out.is_file() and out.stat().st_size > 0 and _xvg_has_numeric_rows(out):
        return out

    candidates: List[str] = []
    env_stdin = os.environ.get(_RMS_ENV)
    if env_stdin is not None and env_stdin.strip():
        candidates.append(env_stdin if env_stdin.endswith("\n") else env_stdin + "\n")
    # Typical: 3=C-alpha, 4=backbone, 1=Protein, 2=Protein-H, 0=System (last resort)
    candidates.extend(
        [
            "3\n3\n",
            "4\n4\n",
            "1\n1\n",
            "2\n2\n",
            "0\n0\n",
        ]
    )

    last_err = ""
    for stdin in candidates:
        if out.is_file():
            try:
                out.unlink()
            except OSError:
                pass
        r = _run_gmx(
            gmx_bin,
            job_dir,
            ["rms", "-s", tpr_name, "-f", xtc_name, "-o", out_name, "-tu", "ps"],
            stdin=stdin,
        )
        last_err = (r.stderr or "")[-400:]
        if r.returncode == 0 and out.is_file() and _xvg_has_numeric_rows(out):
            logger.info(
                "gmx rms OK in %s (stdin %r)",
                job_dir,
                stdin.replace("\n", "\\n"),
            )
            return out
    logger.warning("gmx rms failed for all index guesses in %s: %s", job_dir, last_err)
    return None


def extract_energy_xvgs(
    job_dir: Path,
    *,
    gmx_bin: str = "gmx",
    edr_name: str = "md.edr",
) -> Dict[str, Optional[Path]]:
    """Potential and temperature series from energy file."""
    edr = job_dir / edr_name
    out_pot = job_dir / "potential.xvg"
    out_temp = job_dir / "temperature.xvg"
    if not edr.is_file():
        return {"potential_xvg": None, "temperature_xvg": None}

    def _one(term: str, dest: Path) -> Optional[Path]:
        if dest.is_file() and dest.stat().st_size > 0:
            return dest
        stdin = f"{term}\n0\n"
        r = _run_gmx(
            gmx_bin,
            job_dir,
            ["energy", "-f", edr_name, "-o", dest.name],
            stdin=stdin,
        )
        if r.returncode != 0 or not dest.is_file():
            logger.warning("gmx energy (%s) failed in %s", term, job_dir)
            return None
        return dest

    return {
        "potential_xvg": _one("Potential", out_pot),
        "temperature_xvg": _one("Temperature", out_temp),
    }


def extract_rmsf_xvg(
    job_dir: Path,
    *,
    gmx_bin: str = "gmx",
    tpr_name: str = "md.tpr",
    xtc_name: str = "md.xtc",
    out_name: str = "rmsf.xvg",
) -> Optional[Path]:
    tpr = job_dir / tpr_name
    xtc = job_dir / xtc_name
    out = job_dir / out_name
    if not tpr.is_file() or not xtc.is_file():
        return None
    if out.is_file() and out.stat().st_size > 0 and _xvg_has_numeric_rows(out):
        return out

    candidates: List[str] = []
    env_stdin = os.environ.get(_RMSF_ENV)
    if env_stdin is not None and env_stdin.strip():
        candidates.append(env_stdin if env_stdin.endswith("\n") else env_stdin + "\n")
    candidates.extend(["3\n", "4\n", "1\n", "2\n", "0\n"])

    for stdin in candidates:
        if out.is_file():
            try:
                out.unlink()
            except OSError:
                pass
        r = _run_gmx(
            gmx_bin,
            job_dir,
            ["rmsf", "-s", tpr_name, "-f", xtc_name, "-o", out_name],
            stdin=stdin,
        )
        if r.returncode == 0 and out.is_file() and _xvg_has_numeric_rows(out, min_rows=2):
            logger.info(
                "gmx rmsf OK in %s (stdin %r)",
                job_dir,
                stdin.replace("\n", "\\n"),
            )
            return out
    return None


def ensure_observables_for_job_dir(
    job_dir: Path,
    *,
    gmx_bin: str,
    extract: bool = True,
) -> Dict[str, Any]:
    """
    Return absolute paths for rmsd / energy / temp xvg when available.
    If ``extract`` and GROMACS is present, generate missing series from md.tpr/md.xtc/md.edr.
    """
    job_dir = Path(job_dir)
    meta: Dict[str, Any] = {"job_dir": str(job_dir.resolve())}
    rmsd = job_dir / "rmsd.xvg"
    if extract:
        p = extract_rmsd_xvg(job_dir, gmx_bin=gmx_bin)
        if p:
            rmsd = p
    en = extract_energy_xvgs(job_dir, gmx_bin=gmx_bin) if extract else {}
    pot = en.get("potential_xvg") or (job_dir / "potential.xvg")
    tmp = en.get("temperature_xvg") or (job_dir / "temperature.xvg")
    rmsf = extract_rmsf_xvg(job_dir, gmx_bin=gmx_bin) if extract else None
    if rmsf is None:
        cand = job_dir / "rmsf.xvg"
        rmsf = cand if cand.is_file() else None

    meta["rmsd_xvg"] = str(rmsd.resolve()) if rmsd.is_file() else None
    meta["energy_xvg"] = str(pot.resolve()) if isinstance(pot, Path) and pot.is_file() else None
    meta["temp_xvg"] = str(tmp.resolve()) if isinstance(tmp, Path) and tmp.is_file() else None
    meta["rmsf_xvg"] = str(rmsf.resolve()) if rmsf and rmsf.is_file() else None
    return meta
