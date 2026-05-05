"""GROMACS backend runner.

Pipeline: validate/stage inputs → pdb2gmx → editconf → solvate → genion → energy minimization
→ NVT → NPT → production MDP/grompp → ``mdrun`` (standard) or :class:`AEXEngine` (AEX mode)
→ :class:`OutputPackager`. Optional ligand: ``ligand.itp`` / ``ligand.mol2`` merged into
``topol.top``. Runtime is estimated via :class:`RuntimeEstimator` before execution.
"""

import hashlib
import json
import logging
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from app.config import settings
from app.core.storage import materialize_uri

from .pdb_sanitize import prepare_receptor_pdb_for_gromacs
from .mdp_generator import MDPGenerator
from .topology_builder import merge_ligand_topology
from .estimator import RuntimeEstimator
from .aex_engine import AEXEngine
from .output_packager import OutputPackager

logger = logging.getLogger(__name__)


@dataclass
class DynamicsInputs:
    protein_pdb: str
    forcefield: str = "amber99sb-ildn"
    water_model: str = "tip3p"
    box_type: str = "dodecahedron"
    box_distance: float = 1.0
    em_steps: int = 50000
    nvt_steps: int = 100000
    npt_steps: int = 100000
    production_steps: int = 5000000
    dt: float = 0.002
    temperature: float = 300.0
    pressure: float = 1.0
    thermostat: str = "v-rescale"
    barostat: str = "Parrinello-Rahman"
    tau_t: float = 0.1
    tau_p: float = 2.0
    coulombtype: str = "PME"
    rcoulomb: float = 1.0
    rvdw: float = 1.0
    fourierspacing: float = 0.16
    constraints: str = "h-bonds"
    lincs_iter: int = 1
    lincs_order: int = 4
    nstxout: int = 500
    nstvout: int = 500
    nstfout: int = 0
    nstlog: int = 500
    nstenergy: int = 500
    nstxout_compressed: int = 500
    ligand_itp: Optional[str] = None
    ligand_mol2: Optional[str] = None
    use_aex: bool = False
    aex_fidelity_target: float = 0.95
    aex_max_speedup: float = 10.0
    posre: bool = True
    gen_vel: bool = True
    continuation: bool = False
    custom_mdp_overrides: Dict = field(default_factory=dict)
    job_id: str = ""
    output_dir: str = "/tmp/caly360_md"


@dataclass
class DynamicsResult:
    job_id: str
    success: bool
    output_dir: str
    zip_path: Optional[str]
    trajectory_xtc: Optional[str] = None
    energy_edr: Optional[str] = None
    structure_gro: Optional[str] = None
    topology_tpr: Optional[str] = None
    log_file: Optional[str] = None
    wall_time_seconds: float = 0.0
    simulated_time_ns: float = 0.0
    performance_ns_per_day: float = 0.0
    aex_speedup_achieved: float = 1.0
    aex_report: Optional[dict] = None
    error_message: Optional[str] = None


class GROMACSRunner:
    def __init__(self, inputs: DynamicsInputs):
        self.inputs = inputs
        self._gmx_bin = settings.gromacs_executable()
        self.work_dir = Path(inputs.output_dir) / inputs.job_id
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.mdp_gen = MDPGenerator(inputs)
        self.estimator = RuntimeEstimator(inputs)
        self._manifest: List[Dict] = []
        self._progress_callback = None

    def _report_progress(self, step: str, pct: int):
        if self._progress_callback:
            try:
                self._progress_callback(step, pct)
            except Exception:
                pass

    def run(self, progress_callback=None) -> DynamicsResult:
        self._progress_callback = progress_callback
        start_time = time.time()
        logger.info("[%s] Starting GROMACS run in %s", self.inputs.job_id, self.work_dir)
        try:
            est = self.estimator.estimate()
            logger.info(
                "[%s] Estimated runtime: %.1fh | AEX speedup: %.1fx",
                self.inputs.job_id,
                est["hours"],
                est.get("aex_speedup", 1.0),
            )
            pdb_path = self._stage_input(self.inputs.protein_pdb, "input.pdb")
            self._log("pdb2gmx")
            self._report_progress("pdb2gmx", 5)
            self._run_gmx(
                [
                    "pdb2gmx",
                    "-f",
                    str(pdb_path),
                    "-o",
                    "processed.gro",
                    "-p",
                    "topol.top",
                    "-ff",
                    self.inputs.forcefield,
                    "-water",
                    self.inputs.water_model,
                    "-ignh",
                    "-missing",
                    "-merge",
                    "all",
                ]
            )
            if self.inputs.ligand_itp and self.inputs.ligand_mol2:
                self._integrate_ligand()
            self._log("editconf")
            self._report_progress("editconf", 15)
            self._run_gmx(
                [
                    "editconf",
                    "-f",
                    "processed.gro",
                    "-o",
                    "boxed.gro",
                    "-c",
                    "-d",
                    str(self.inputs.box_distance),
                    "-bt",
                    self.inputs.box_type,
                ]
            )
            self._log("solvate")
            self._report_progress("solvate", 25)
            self._run_gmx(
                [
                    "solvate",
                    "-cp",
                    "boxed.gro",
                    "-cs",
                    "spc216.gro",
                    "-o",
                    "solvated.gro",
                    "-p",
                    "topol.top",
                ]
            )
            self._log("genion")
            self._report_progress("genion", 35)
            ions_mdp = self.mdp_gen.write_ions_mdp(self.work_dir)
            self._run_gmx(
                [
                    "grompp",
                    "-f",
                    str(ions_mdp),
                    "-c",
                    "solvated.gro",
                    "-p",
                    "topol.top",
                    "-o",
                    "ions.tpr",
                ]
            )
            self._run_gmx_stdin(
                [
                    "genion",
                    "-s",
                    "ions.tpr",
                    "-o",
                    "ionized.gro",
                    "-p",
                    "topol.top",
                    "-pname",
                    "NA",
                    "-nname",
                    "CL",
                    "-neutral",
                ],
                stdin="SOL\n",
            )
            self._log("energy minimization")
            self._report_progress("energy_min", 45)
            em_mdp = self.mdp_gen.write_em_mdp(self.work_dir)
            self._run_gmx(
                ["grompp", "-f", str(em_mdp), "-c", "ionized.gro", "-p", "topol.top", "-o", "em.tpr"]
            )
            self._run_gmx(["mdrun", "-v", "-deffnm", "em"])
            self._log("NVT equilibration")
            self._report_progress("nvt", 55)
            nvt_mdp = self.mdp_gen.write_nvt_mdp(self.work_dir)
            self._run_gmx(
                [
                    "grompp",
                    "-f",
                    str(nvt_mdp),
                    "-c",
                    "em.gro",
                    "-r",
                    "em.gro",
                    "-p",
                    "topol.top",
                    "-o",
                    "nvt.tpr",
                ]
            )
            self._run_gmx(["mdrun", "-deffnm", "nvt"])
            self._log("NPT equilibration")
            self._report_progress("npt", 65)
            npt_mdp = self.mdp_gen.write_npt_mdp(self.work_dir)
            self._run_gmx(
                [
                    "grompp",
                    "-f",
                    str(npt_mdp),
                    "-c",
                    "nvt.gro",
                    "-r",
                    "nvt.gro",
                    "-t",
                    "nvt.cpt",
                    "-p",
                    "topol.top",
                    "-o",
                    "npt.tpr",
                ]
            )
            self._run_gmx(["mdrun", "-deffnm", "npt"])
            self._log("production MD")
            self._report_progress("production", 75)
            prod_mdp = self.mdp_gen.write_production_mdp(self.work_dir)
            self._run_gmx(
                [
                    "grompp",
                    "-f",
                    str(prod_mdp),
                    "-c",
                    "npt.gro",
                    "-t",
                    "npt.cpt",
                    "-p",
                    "topol.top",
                    "-o",
                    "md.tpr",
                ]
            )
            aex_report = None
            if self.inputs.use_aex:
                self._report_progress("aex_mdrun", 85)
                aex_engine = AEXEngine(
                    work_dir=self.work_dir,
                    inputs=self.inputs,
                    tpr_file="md.tpr",
                    gmx_bin=self._gmx_bin,
                )
                aex_report = aex_engine.run()
            else:
                self._report_progress("mdrun", 85)
                self._run_gmx(["mdrun", "-deffnm", "md", "-ntmpi", "1", "-ntomp", "4"])
            self._report_progress("packaging", 95)
            self._write_run_manifest()
            packager = OutputPackager(self.work_dir, self.inputs.job_id)
            zip_path = packager.package()
            self._report_progress("complete", 100)
            wall_time = time.time() - start_time
            sim_time_ns = (self.inputs.production_steps * self.inputs.dt) / 1000.0
            return DynamicsResult(
                job_id=self.inputs.job_id,
                success=True,
                output_dir=str(self.work_dir),
                zip_path=zip_path,
                trajectory_xtc=str(self.work_dir / "md.xtc"),
                energy_edr=str(self.work_dir / "md.edr"),
                structure_gro=str(self.work_dir / "md.gro"),
                topology_tpr=str(self.work_dir / "md.tpr"),
                log_file=str(self.work_dir / "md.log"),
                wall_time_seconds=wall_time,
                simulated_time_ns=sim_time_ns,
                aex_speedup_achieved=aex_report.get("speedup", 1.0) if aex_report else 1.0,
                aex_report=aex_report,
            )
        except Exception as e:
            logger.error("[%s] GROMACS run failed: %s", self.inputs.job_id, e, exc_info=True)
            return DynamicsResult(
                job_id=self.inputs.job_id,
                success=False,
                output_dir=str(self.work_dir),
                zip_path=None,
                error_message=str(e),
                wall_time_seconds=time.time() - start_time,
            )

    def _run_gmx(self, args: List[str], **kwargs):
        cmd = [self._gmx_bin] + args
        logger.debug("[%s] Running: %s", self.inputs.job_id, " ".join(cmd))
        result = subprocess.run(cmd, cwd=self.work_dir, capture_output=True, text=True, **kwargs)
        if result.returncode != 0:
            raise RuntimeError(
                f"GROMACS command failed: {' '.join(args)}\nSTDERR: {result.stderr[-2000:]}"
            )
        self._manifest.append({"step": args[0], "cmd": " ".join(args), "returncode": result.returncode})

    def _run_gmx_stdin(self, args: List[str], stdin: str):
        cmd = [self._gmx_bin] + args
        result = subprocess.run(cmd, cwd=self.work_dir, input=stdin, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"GROMACS command failed: {' '.join(args)}\nSTDERR: {result.stderr[-2000:]}"
            )

    def _stage_input(self, src: str, dest: str) -> Path:
        dest_path = self.work_dir / dest
        materialize_uri(src, dest_path)
        n_het, n_his = prepare_receptor_pdb_for_gromacs(dest_path)
        if n_het or n_his:
            logger.info(
                "[%s] PDB prep: removed %d HETATM line(s), converted %d incomplete HIS→ALA",
                self.inputs.job_id,
                n_het,
                n_his,
            )
        return dest_path

    def _integrate_ligand(self):
        materialize_uri(self.inputs.ligand_itp, self.work_dir / "ligand.itp")
        if self.inputs.ligand_mol2:
            materialize_uri(self.inputs.ligand_mol2, self.work_dir / "ligand.mol2")
        merge_ligand_topology(self.work_dir / "topol.top", self.work_dir / "ligand.itp")

    def _log(self, step: str):
        logger.info("[%s] ── %s ──", self.inputs.job_id, step.upper())

    def _write_run_manifest(self) -> None:
        """Layer-6 audit: deterministic command trace + environment fingerprint (spec reproducibility)."""
        base: Dict[str, Any] = {
            "job_id": self.inputs.job_id,
            "gmx_bin": self._gmx_bin,
            "commands": list(self._manifest),
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
            },
        }
        fp = hashlib.sha256(json.dumps(base, sort_keys=True).encode("utf-8")).hexdigest()
        payload = {**base, "execution_fingerprint_sha256": fp}
        (self.work_dir / "gromacs_run_manifest.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def extract_observables(self, gmx_bin: Optional[str] = None) -> Dict[str, Any]:
        """Post-run: build RMSD / energy / temperature `.xvg` files under ``work_dir`` when possible."""
        from .gromacs_extract import ensure_observables_for_job_dir

        return ensure_observables_for_job_dir(
            self.work_dir,
            gmx_bin=gmx_bin or self._gmx_bin,
            extract=True,
        )
