# Dynamics

Standalone DYNAMICS handoff package for CALY360.

Everything needed for the molecular-dynamics side now lives inside this folder:

- `backend/`
  FastAPI backend, GROMACS runner, AEX engine, storage, DB wiring, workers, and tests

- `frontend/`
  the DYNAMICS UI, mode selector, upload form, polling, download flow, and API client

- `deployment/`
  Docker Compose, backend/frontend Dockerfiles, and nginx config for a standalone bring-up

- `data/`
  DYNAMICS and AEX validation manifests plus the bundled test system

- `outputs/`
  packaged MD/AEX output and validation output directories

- `.tools/`
  bundled local GROMACS toolchain used by the standalone package when present

- `python_package/`
  direct Python package mirror of the DYNAMICS runtime modules

Also read:

- `AEX_FORMAL_SPEC.txt`
- `MODULE_MAP.txt`
- `README.txt`
- `manifest.json`

## What This Folder Covers

This package maps directly to the DYNAMICS sections of the spec:

- `4.1 GROMACS Backend Integration`
  `backend/app/dynamics/gromacs_runner.py`
  `backend/app/dynamics/mdp_generator.py`
  `backend/app/dynamics/topology_builder.py`
  `backend/app/dynamics/output_packager.py`
  `backend/app/dynamics/estimator.py`

- `4.2 Input Schema`
  `backend/app/api/dynamics/schemas.py`
  `frontend/src/components/dynamics/SimulationForm.tsx`
  `frontend/src/types/dynamics.ts`

- `4.3 AEX (Adaptive Execution) Engine`
  `backend/app/dynamics/aex_engine.py`
  `backend/app/dynamics/aex_curvature.py`
  `backend/app/dynamics/aex_information.py`
  `backend/app/dynamics/aex_stability.py`
  `backend/app/validation/aex/`

- `4.4 Full Python Implementation`
  `backend/app/dynamics/`

## Handoff Notes

- This folder is now a real standalone package, not a symlink-only mirror.
- Root-workspace DYNAMICS source was removed so the DYNAMICS codepath lives here.
- The bundled GROMACS binary is discovered from `.tools/` first, then PATH as a fallback.
- The full path inventory is recorded in `manifest.json`.
