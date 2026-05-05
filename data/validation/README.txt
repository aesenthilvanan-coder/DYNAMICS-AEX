DYNAMICS validation inputs

1) dynamics_benchmarks.json
   Benchmark systems with optional job_dir and/or extracted GROMACS .xvg paths
   (RMSD, energy, temperature).
   Run: python3 scripts/run_dynamics_validation.py

2) aex_pairs.json
   Baseline-vs-AEX job directory pairs. Each AEX side should contain aex_report.json.
   Run: python3 scripts/run_aex_validation.py

3) aex_empirical_pairs.json
   Optional real completed-job pairs for repeated AEX fidelity and speed checks.

Artifacts land under outputs/validation/{dynamics,aex}/.
