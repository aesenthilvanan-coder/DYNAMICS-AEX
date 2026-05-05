# DRD2 minimal test system

## Purpose

Provide a **small, reproducible** input deck for CALY360 dynamics and paired AEX benchmarks. This is **not** a claim of fully parameterized orthosteric/allosteric ligand MD.

## Contents

| File | Role |
|------|------|
| `metadata.json` | System id, expected filenames, limitations |
| `receptor.pdb` | **Download** with `scripts/fetch_d2r_receptor.py` (default: PDB 6CM4) |
| `ligand.mol2` | Optional geometry placeholder for future topology work |

## Running real MD

1. `python scripts/fetch_d2r_receptor.py` (from repo root)
2. `python scripts/run_aex_paired_benchmark.py --receptor-pdb data/test_systems/d2r_ligand/receptor.pdb`
3. Point `data/validation/dynamics_benchmarks.json` at the produced `job_dir` or merge printed paths.

Short simulations are **minimal real-compute checks** only.

## If `gmx rms` / `gmx rmsf` group indices differ

Validation auto-extraction tries several common index choices. To force stdin explicitly:

```bash
export CALY360_GMX_RMS_STDIN=$'5\n5\n'    # fit group, then RMSD group
export CALY360_GMX_RMSF_STDIN=$'5\n'
```

See `backend/app/validation/dynamics/gromacs_extract.py`.
