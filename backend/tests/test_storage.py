"""Local storage backend round-trip."""

from pathlib import Path

from app.core.storage import LocalStorageBackend


def test_local_storage_write_and_materialize(tmp_path: Path):
    backend = LocalStorageBackend(tmp_path)
    uri = backend.write_bytes("job1/input.pdb", b"ATOM")
    assert Path(uri).is_file()
    dest = tmp_path / "staged.pdb"
    backend.materialize_to(uri, dest)
    assert dest.read_bytes() == b"ATOM"
