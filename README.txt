CALY360 — DYNAMICS handoff package
==================================

This folder is the standalone home for all molecular-dynamics work:

  backend/         API, runner, AEX math, worker, DB glue, tests
  frontend/        upload form, mode selector, polling, downloads
  deployment/      compose + Dockerfiles + nginx for standalone startup
  data/            validation manifests + bundled test system
  outputs/         generated MD/AEX artifacts and validation outputs
  .tools/          bundled local GROMACS toolchain
  python_package/  direct Python-package mirror of the DYNAMICS modules

Also read:

  manifest.json       complete file inventory
  AEX_FORMAL_SPEC.txt full AEX formal system
  MODULE_MAP.txt      spec section to file mapping

This package is no longer a symlink-only mirror. It is the actual DYNAMICS handoff tree.
