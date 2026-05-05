"""MDP file generator for GROMACS.

Generates MDP parameter files for each phase: ions (steep, nsteps=0), energy minimization,
NVT, NPT, and production. Honors ``custom_mdp_overrides`` on :class:`~app.dynamics.gromacs_runner.DynamicsInputs`.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gromacs_runner import DynamicsInputs


class MDPGenerator:
    def __init__(self, inputs: "DynamicsInputs"):
        self.inp = inputs

    def _base_params(self) -> dict:
        i = self.inp
        return {
            "cutoff-scheme": "Verlet",
            "coulombtype": i.coulombtype,
            "rcoulomb": i.rcoulomb,
            "rvdw": i.rvdw,
            "fourierspacing": i.fourierspacing,
            "pme-order": 4,
            "ewald-rtol": "1e-5",
            "constraints": i.constraints,
            "lincs-iter": i.lincs_iter,
            "lincs-order": i.lincs_order,
            "ns-type": "grid",
            "nstlist": 10,
            "periodic-molecules": "no",
        }

    def _write_mdp(self, params: dict, path: Path) -> Path:
        for k, v in self.inp.custom_mdp_overrides.items():
            params[k] = v
        lines = [f"{k:<35} = {v}" for k, v in params.items()]
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")
        return path

    def write_ions_mdp(self, work_dir: Path) -> Path:
        params = {"integrator": "steep", "nsteps": 0, "emtol": 1000.0, **self._base_params()}
        return self._write_mdp(params, work_dir / "ions.mdp")

    def write_em_mdp(self, work_dir: Path) -> Path:
        params = {
            "integrator": "steep",
            "emtol": 1000.0,
            "emstep": 0.01,
            "nsteps": self.inp.em_steps,
            "nstxout": 0,
            "nstvout": 0,
            "nstenergy": 500,
            "nstlog": 500,
            **self._base_params(),
        }
        return self._write_mdp(params, work_dir / "em.mdp")

    def write_nvt_mdp(self, work_dir: Path) -> Path:
        i = self.inp
        params = {
            "integrator": "md",
            "dt": i.dt,
            "nsteps": i.nvt_steps,
            "nstxout": i.nstxout,
            "nstvout": i.nstvout,
            "nstenergy": i.nstenergy,
            "nstlog": i.nstlog,
            "nstxout-compressed": i.nstxout_compressed,
            "tcoupl": i.thermostat,
            "tc-grps": "Protein Non-Protein",
            "tau-t": f"{i.tau_t} {i.tau_t}",
            "ref-t": f"{i.temperature} {i.temperature}",
            "pcoupl": "no",
            "gen-vel": "yes" if i.gen_vel else "no",
            "gen-temp": i.temperature,
            "gen-seed": -1,
            "define": "-DPOSRES" if i.posre else "",
            **self._base_params(),
        }
        return self._write_mdp(params, work_dir / "nvt.mdp")

    def write_npt_mdp(self, work_dir: Path) -> Path:
        i = self.inp
        params = {
            "integrator": "md",
            "dt": i.dt,
            "nsteps": i.npt_steps,
            "nstxout": i.nstxout,
            "nstvout": i.nstvout,
            "nstenergy": i.nstenergy,
            "nstlog": i.nstlog,
            "nstxout-compressed": i.nstxout_compressed,
            "tcoupl": i.thermostat,
            "tc-grps": "Protein Non-Protein",
            "tau-t": f"{i.tau_t} {i.tau_t}",
            "ref-t": f"{i.temperature} {i.temperature}",
            "pcoupl": i.barostat,
            "tau-p": i.tau_p,
            "ref-p": i.pressure,
            "compressibility": "4.5e-5",
            "continuation": "yes" if i.continuation else "no",
            "gen-vel": "no",
            "define": "-DPOSRES" if i.posre else "",
            **self._base_params(),
        }
        return self._write_mdp(params, work_dir / "npt.mdp")

    def write_production_mdp(self, work_dir: Path) -> Path:
        i = self.inp
        params = {
            "integrator": "md",
            "dt": i.dt,
            "nsteps": i.production_steps,
            "nstxout": i.nstxout,
            "nstvout": i.nstvout,
            "nstfout": i.nstfout,
            "nstenergy": i.nstenergy,
            "nstlog": i.nstlog,
            "nstxout-compressed": i.nstxout_compressed,
            "tcoupl": i.thermostat,
            "tc-grps": "Protein Non-Protein",
            "tau-t": f"{i.tau_t} {i.tau_t}",
            "ref-t": f"{i.temperature} {i.temperature}",
            "pcoupl": i.barostat,
            "tau-p": i.tau_p,
            "ref-p": i.pressure,
            "compressibility": "4.5e-5",
            "continuation": "yes",
            "gen-vel": "no",
            **self._base_params(),
        }
        return self._write_mdp(params, work_dir / "md.mdp")
