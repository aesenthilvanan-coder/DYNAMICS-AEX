import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["module"] == "dynamics"
    assert body["database"] == "disabled"
    assert "gromacs_bin" in body


def test_ready_without_database():
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json().get("status") == "ready"


def test_jobs_index():
    r = client.get("/api/v1/jobs")
    assert r.status_code == 200
    body = r.json()
    assert "dynamics" in body
    assert "unified" in body
    assert "storage" in body


def test_dynamics_local_bootstrap_json():
    r = client.get("/api/v1/dynamics/local-bootstrap.json")
    assert r.status_code == 200
    body = r.json()
    assert body.get("version") >= 1
    assert "endpoints" in body
    assert "env_hints" in body


def test_dynamics_local_bootstrap_sh():
    r = client.get("/api/v1/dynamics/local-bootstrap.sh")
    assert r.status_code == 200
    assert "docker compose" in r.text
    assert "worker_dynamics" in r.text


def test_dynamics_execution_health():
    r = client.get("/api/v1/dynamics/health-execution")
    assert r.status_code == 200
    body = r.json()
    assert "gromacs" in body
    assert "broker" in body
    assert "execution_mode" in body
    assert "inprocess_jobs" in body
