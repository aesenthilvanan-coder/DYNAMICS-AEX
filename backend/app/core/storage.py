"""Object storage: local filesystem or S3-compatible (MinIO, AWS)."""

from __future__ import annotations

import logging
import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_S3_URI = re.compile(r"^s3://([^/]+)/(.+)$")


class StorageBackend(ABC):
    """Write uploads and optionally materialize to a local path for GROMACS."""

    @abstractmethod
    def write_bytes(self, rel_key: str, data: bytes) -> str:
        """Return URI or absolute path string the worker understands."""

    @abstractmethod
    def materialize_to(self, uri: str, dest_path: Path) -> None:
        """Copy or download uri into dest_path (file)."""


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path):
        self.root = Path(root)

    def write_bytes(self, rel_key: str, data: bytes) -> str:
        path = (self.root / rel_key).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    def materialize_to(self, uri: str, dest_path: Path) -> None:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(uri, dest_path)


class S3StorageBackend(StorageBackend):
    def __init__(
        self,
        bucket: str,
        prefix: str,
        *,
        endpoint_url: Optional[str] = None,
        region: Optional[str] = None,
    ):
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        import boto3  # lazy

        session = boto3.session.Session()
        self._client = session.client(
            "s3",
            endpoint_url=endpoint_url or None,
            region_name=region or "us-east-1",
        )

    def _full_key(self, rel_key: str) -> str:
        rel_key = rel_key.lstrip("/")
        return f"{self.prefix}/{rel_key}" if self.prefix else rel_key

    def write_bytes(self, rel_key: str, data: bytes) -> str:
        key = self._full_key(rel_key)
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return f"s3://{self.bucket}/{key}"

    def materialize_to(self, uri: str, dest_path: Path) -> None:
        m = _S3_URI.match(uri)
        if not m:
            raise ValueError(f"Not an s3 URI: {uri}")
        bucket, key = m.group(1), m.group(2)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(bucket, key, str(dest_path))


_backend: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    global _backend
    if _backend is not None:
        return _backend
    backend = (settings.STORAGE_BACKEND or "local").strip().lower()
    if backend == "s3":
        if not settings.S3_BUCKET.strip():
            logger.warning("STORAGE_BACKEND=s3 but S3_BUCKET empty; falling back to local")
            _backend = LocalStorageBackend(Path(settings.LOCAL_UPLOAD_ROOT))
            return _backend
        _backend = S3StorageBackend(
            bucket=settings.S3_BUCKET.strip(),
            prefix=settings.S3_PREFIX.strip(),
            endpoint_url=settings.S3_ENDPOINT_URL.strip() or None,
            region=settings.AWS_REGION.strip() or None,
        )
        return _backend
    _backend = LocalStorageBackend(Path(settings.LOCAL_UPLOAD_ROOT))
    return _backend


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def materialize_uri(uri: str, dest_path: Path) -> None:
    get_storage().materialize_to(uri, dest_path)
