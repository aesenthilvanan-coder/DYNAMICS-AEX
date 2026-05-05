"""Validation pipeline writes expected artifacts."""

import json
from pathlib import Path

from app.dynamics.evaluate_dynamics import run_dynamics_validation


def test_dynamics_validation_writes_summary(tmp_path: Path):
    job = tmp_path / "md_job"
    job.mkdir()
    (job / "rmsd.xvg").write_text(
        "# test\n0.0 0.1\n0.002 0.11\n0.004 0.12\n",
        encoding="utf-8",
    )
    bench = tmp_path / "bench.json"
    bench.write_text(
        json.dumps(
            {
                "systems": [
                    {
                        "id": "s1",
                        "job_dir": str(job),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    run_dynamics_validation(benchmark_json=bench, output_root=out, auto_extract_from_job_dir=False)
    assert (out / "dynamics" / "dynamics_validation_summary.json").is_file()
    assert (out / "dynamics" / "failure_summary.csv").is_file()
    summary = json.loads((out / "dynamics" / "dynamics_validation_summary.json").read_text(encoding="utf-8"))
    assert summary.get("n_real_md_systems") == 1
    assert summary.get("n_missing_traces") == 0
    assert (out / "dynamics" / "dynamics_validation_report.md").is_file()
