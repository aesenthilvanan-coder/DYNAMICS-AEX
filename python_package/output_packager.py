"""Bundle MD outputs for download."""

import zipfile
from pathlib import Path
from typing import List


class OutputPackager:
    def __init__(self, work_dir: Path, job_id: str):
        self.work_dir = Path(work_dir)
        self.job_id = job_id

    def package(self) -> str:
        zip_path = self.work_dir / f"{self.job_id}_outputs.zip"
        patterns: List[str] = [
            "*.gro",
            "*.xtc",
            "*.edr",
            "*.log",
            "*.tpr",
            "*.mdp",
            "*_energy.xvg",
            "aex_report.json",
            "gromacs_run_manifest.json",
            "topol.top",
        ]
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            added = set()
            for pat in patterns:
                for p in self.work_dir.glob(pat):
                    if p.is_file() and p.name not in added:
                        zf.write(p, arcname=p.name)
                        added.add(p.name)
        return str(zip_path)
