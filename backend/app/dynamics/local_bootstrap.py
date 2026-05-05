"""One-file local environment bootstrap for DYNAMICS (Docker + optional native GROMACS hints)."""

from __future__ import annotations

import textwrap


def render_bootstrap_shell_script() -> str:
    """POSIX shell: pull/build Caly360 stack services that run GROMACS MD workers."""
    return textwrap.dedent(
        r"""
        #!/usr/bin/env bash
        # Caly360 DYNAMICS — local dependency bootstrap (generated; safe to re-run)
        set -euo pipefail

        ROOT="${CALY360_ROOT:-}"
        if [[ -z "$ROOT" ]]; then
          echo "Set CALY360_ROOT to your repository clone, e.g. export CALY360_ROOT=\"\$HOME/Caly360 Project\""
          exit 1
        fi
        cd "$ROOT"

        echo "==> [1/3] Ensuring Docker Compose stack (api, redis, db, worker_dynamics)…"
        if ! command -v docker >/dev/null 2>&1; then
          echo "Docker not found. Install Docker Desktop or Engine, then re-run this script."
          exit 1
        fi
        docker compose version >/dev/null 2>&1 || { echo "Install Docker Compose v2 plugin."; exit 1; }

        docker compose build api worker_dynamics
        docker compose up -d redis db
        echo "Waiting for Postgres/Redis healthchecks (up to ~60s)…"
        sleep 15
        docker compose up -d api worker_dynamics

        echo "==> [2/3] Optional: native GROMACS for local CLI (skip if you only use containers)"
        if command -v conda >/dev/null 2>&1; then
          echo "    conda install -y -c conda-forge gromacs  # run in a dedicated env if desired"
        elif command -v mamba >/dev/null 2>&1; then
          echo "    mamba install -y -c conda-forge gromacs"
        else
          echo "    No conda/mamba — use OS packages or https://www.gromacs.org for native gmx"
        fi

        echo "==> [3/3] Done. API: http://localhost:8000  ·  MD worker queue: dynamics"
        echo "    Frontend (if using Vite dev): set VITE_API_URL=http://localhost:8000/api/v1"
        """
    ).strip() + "\n"


def bootstrap_manifest() -> dict:
    return {
        "version": 1,
        "description": "Downloads/builds Caly360 Docker images and starts dynamics worker dependencies.",
        "script_filename": "caly360-dynamics-local-setup.sh",
        "endpoints": {
            "shell_script": "/api/v1/dynamics/local-bootstrap.sh",
            "health_gromacs": "/api/v1/dynamics/health-md",
        },
        "env_hints": {
            "CALY360_ROOT": "Absolute path to this repository on your machine",
            "VITE_API_URL": "http://localhost:8000/api/v1 for local Vite dev",
        },
    }
