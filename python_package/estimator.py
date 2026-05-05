"""Runtime estimator for GROMACS simulations.

Wall-clock estimate from PDB atom count, hardware tier (CPU vs single/multi-GPU via ``nvidia-smi``),
simulated length (production + equilibration), and optional AEX speedup factor.
"""

from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .gromacs_runner import DynamicsInputs


class RuntimeEstimator:
    PERFORMANCE_BENCHMARKS = {
        "cpu_only": {"small": 5.0, "medium": 2.0, "large": 0.5},
        "gpu_single": {"small": 50.0, "medium": 25.0, "large": 8.0},
        "gpu_multi": {"small": 150.0, "medium": 80.0, "large": 30.0},
    }

    def __init__(self, inputs: "DynamicsInputs"):
        self.inputs = inputs

    def _count_atoms(self) -> int:
        try:
            count = 0
            with open(self.inputs.protein_pdb) as f:
                for line in f:
                    if line.startswith(("ATOM", "HETATM")):
                        count += 1
            return count
        except Exception:
            return 10000

    def _detect_hardware(self) -> str:
        import shutil
        import subprocess

        if shutil.which("nvidia-smi"):
            try:
                r = subprocess.run(
                    ["nvidia-smi", "--query-gpu=count", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                n_gpus = int(r.stdout.strip().split("\n")[0] or 0)
                return "gpu_multi" if n_gpus > 1 else "gpu_single"
            except Exception:
                pass
        return "cpu_only"

    def estimate(self) -> Dict:
        n_atoms = self._count_atoms()
        hw = self._detect_hardware()
        if n_atoms < 5000:
            size_class = "small"
        elif n_atoms < 50000:
            size_class = "medium"
        else:
            size_class = "large"
        solvated_atoms = n_atoms * 10
        perf_ns_per_day = self.PERFORMANCE_BENCHMARKS[hw][size_class]
        sim_time_ns = (self.inputs.production_steps * self.inputs.dt) / 1000.0
        total_sim_ns = sim_time_ns + (
            (self.inputs.nvt_steps + self.inputs.npt_steps) * self.inputs.dt / 1000.0
        )
        wall_time_days = total_sim_ns / perf_ns_per_day
        wall_time_hours = wall_time_days * 24
        aex_speedup = 1.0
        if self.inputs.use_aex:
            if size_class == "small":
                aex_speedup = 3.0
            elif size_class == "medium":
                aex_speedup = 5.0
            else:
                aex_speedup = self.inputs.aex_max_speedup * 0.7
        aex_wall_hours = wall_time_hours / aex_speedup
        return {
            "n_atoms_protein": n_atoms,
            "n_atoms_solvated_est": solvated_atoms,
            "hardware": hw,
            "sim_time_ns": sim_time_ns,
            "performance_ns_per_day": perf_ns_per_day,
            "estimated_wall_hours": wall_time_hours,
            "aex_speedup": aex_speedup,
            "aex_wall_hours": aex_wall_hours,
            "hours": aex_wall_hours if self.inputs.use_aex else wall_time_hours,
        }
