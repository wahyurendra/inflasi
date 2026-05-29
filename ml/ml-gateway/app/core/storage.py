"""MinIO-backed model artifact store with on-disk + in-memory caching.

Trained artifacts (joblibs, .ckpt) live in the ``inflasi-models`` bucket under
``models/{model_type}/{target_type}/h{horizon}/v{version}/{filename}``.

This module fetches them lazily, caches the bytes to ``MODEL_CACHE_DIR``
(already a Longhorn PVC in production — see the deployment manifest) so a pod
restart doesn't re-download, and keeps **deserialized** objects in an LRU so
hot models avoid the joblib parse cost on every request.

All network I/O is best-effort: a MinIO outage or missing artifact returns
``None`` so the caller (loader) can degrade gracefully and the ensemble
continues with whatever models did load.
"""

from __future__ import annotations

import logging
import os
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any

logger = logging.getLogger("storage")

_DEFAULT_CACHE_DIR = "/models"
_MEM_CACHE_MAX = 96  # ~ enough for 4 lightgbm + 64 per-series prophets/sarimax + headroom


class ModelStore:
    """Fetch + cache model artifacts from MinIO.

    Construction is cheap — the MinIO client is created lazily on first use so
    the service starts cleanly even when MinIO is down.
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        secure: bool | None = None,
        cache_dir: str | None = None,
    ) -> None:
        self.endpoint = endpoint or os.environ.get("MINIO_ENDPOINT", "inflasi-minio:9000")
        self.access_key = access_key or os.environ.get("MINIO_ACCESS_KEY", "")
        self.secret_key = secret_key or os.environ.get("MINIO_SECRET_KEY", "")
        self.bucket = bucket or os.environ.get("MINIO_BUCKET", "inflasi-models")
        env_secure = os.environ.get("MINIO_SECURE", "false").lower() in {"1", "true", "yes"}
        self.secure = env_secure if secure is None else secure
        self.cache_dir = Path(cache_dir or os.environ.get("MODEL_CACHE_DIR", _DEFAULT_CACHE_DIR))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._client: Any = None
        self._client_lock = threading.Lock()
        self._mem: "OrderedDict[str, Any]" = OrderedDict()
        self._mem_lock = threading.Lock()

    # ── Client (lazy) ────────────────────────────────────────

    def _ensure_client(self) -> Any | None:
        if self._client is not None:
            return self._client
        with self._client_lock:
            if self._client is not None:
                return self._client
            try:
                from minio import Minio  # type: ignore
            except Exception:
                logger.exception("minio client unavailable")
                return None
            try:
                self._client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure,
                )
            except Exception:
                logger.exception("failed to construct Minio client")
                return None
        return self._client

    # ── Disk cache ───────────────────────────────────────────

    def _local_path(self, key: str) -> Path:
        # Mirror the remote path under the cache dir; create parent dirs.
        path = self.cache_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def fetch_to_disk(self, key: str) -> Path | None:
        """Download ``key`` to the disk cache if missing; return its local path.

        Returns ``None`` when MinIO is unavailable or the object doesn't exist.
        """
        local = self._local_path(key)
        if local.exists() and local.stat().st_size > 0:
            return local
        client = self._ensure_client()
        if client is None:
            return None
        try:
            client.fget_object(self.bucket, key, str(local))
            return local
        except Exception as e:
            logger.warning("MinIO fetch failed for %s/%s: %s", self.bucket, key, e)
            return None

    # ── In-memory cache ──────────────────────────────────────

    def _mem_get(self, key: str) -> Any:
        with self._mem_lock:
            if key in self._mem:
                self._mem.move_to_end(key)
                return self._mem[key]
        return _MISS

    def _mem_set(self, key: str, value: Any) -> None:
        with self._mem_lock:
            self._mem[key] = value
            self._mem.move_to_end(key)
            while len(self._mem) > _MEM_CACHE_MAX:
                self._mem.popitem(last=False)

    def clear_cache(self) -> None:
        with self._mem_lock:
            self._mem.clear()

    # ── Typed loaders ────────────────────────────────────────

    def load_joblib(self, key: str) -> Any:
        """Fetch + deserialize a joblib artifact. Returns ``None`` on any failure."""
        cached = self._mem_get(key)
        if cached is not _MISS:
            return cached
        path = self.fetch_to_disk(key)
        if path is None:
            return None
        try:
            import joblib  # type: ignore

            obj = joblib.load(path)
            self._mem_set(key, obj)
            return obj
        except Exception:
            logger.exception("joblib.load failed for %s", path)
            return None

    def get_checkpoint_path(self, key: str) -> str | None:
        """Fetch a checkpoint to disk, return its local path string (torch expects str)."""
        path = self.fetch_to_disk(key)
        return str(path) if path else None


# Sentinel for cache miss (None is a valid cached value for "tried-and-failed").
_MISS = object()


_default_store: ModelStore | None = None


def get_store() -> ModelStore:
    """Module-level singleton — built lazily on first call."""
    global _default_store
    if _default_store is None:
        _default_store = ModelStore()
    return _default_store
