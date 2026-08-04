"""GCS-backed model artifact store with on-disk + in-memory caching.

Trained artifacts (joblibs, .ckpt) live in the ``train-ml`` bucket under
``models/{model_type}/{target_type}/h{horizon}/v{version}/{filename}``.

This module fetches them lazily, caches the bytes to ``MODEL_CACHE_DIR``
(already a Longhorn PVC in production — see the deployment manifest) so a pod
restart doesn't re-download, and keeps **deserialized** objects in an LRU so
hot models avoid the joblib parse cost on every request.

All network I/O is best-effort: a GCS outage or missing artifact returns
``None`` so the caller (loader) can degrade gracefully and the ensemble
continues with whatever models did load.
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("storage")

_DEFAULT_CACHE_DIR = "/models"
_MEM_CACHE_MAX = 96  # ~ enough for 4 lightgbm + 64 per-series prophets/sarimax + headroom


class ModelStore:
    """Fetch + cache model artifacts from Google Cloud Storage.

    Construction is cheap — the GCS client is created lazily on first use so
    the service starts cleanly even when GCS is unavailable.
    """

    def __init__(
        self,
        *,
        bucket: str | None = None,
        cache_dir: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.bucket = _bucket_name(bucket or os.environ.get("GCS_BUCKET", "train-ml"))
        self.cache_dir = Path(cache_dir or os.environ.get("MODEL_CACHE_DIR", _DEFAULT_CACHE_DIR))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._client: Any = client
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
                from google.cloud import storage  # type: ignore
            except Exception:
                logger.exception("google-cloud-storage client unavailable")
                return None
            try:
                # Uses Application Default Credentials: Workload Identity on GKE,
                # gcloud ADC locally, or GOOGLE_APPLICATION_CREDENTIALS as fallback.
                self._client = storage.Client()
            except Exception:
                logger.exception("failed to construct GCS client from ADC")
                return None
        return self._client

    # ── Disk cache ───────────────────────────────────────────

    def _local_path(self, bucket: str, key: str) -> Path:
        # Mirror the remote path under the cache dir; create parent dirs.
        path = self.cache_dir / bucket / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def fetch_to_disk(self, key: str) -> Path | None:
        """Download ``key`` to the disk cache if missing; return its local path.

        ``key`` may be a full ``gs://bucket/object`` URI or an object name in
        ``GCS_BUCKET``. Returns ``None`` when GCS is unavailable or the object
        does not exist.
        """
        try:
            bucket, object_key = _split_location(key, self.bucket)
        except ValueError as exc:
            logger.warning("invalid GCS artifact path %r: %s", key, exc)
            return None
        local = self._local_path(bucket, object_key)
        if local.exists() and local.stat().st_size > 0:
            return local
        client = self._ensure_client()
        if client is None:
            return None
        temporary = local.with_name(f".{local.name}.{uuid.uuid4().hex}.part")
        try:
            client.bucket(bucket).blob(object_key).download_to_filename(str(temporary))
            temporary.replace(local)
            return local
        except Exception as e:
            temporary.unlink(missing_ok=True)
            logger.warning("GCS fetch failed for gs://%s/%s: %s", bucket, object_key, e)
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


def _bucket_name(value: str) -> str:
    raw = value.strip().rstrip("/")
    if raw.startswith("gs://"):
        parsed = urlparse(raw)
        if parsed.path not in {"", "/"}:
            raise ValueError("GCS_BUCKET must not include an object prefix")
        raw = parsed.netloc
    if not raw or raw in {".", ".."} or "/" in raw:
        raise ValueError(f"invalid GCS bucket: {value!r}")
    return raw


def _split_location(value: str, default_bucket: str) -> tuple[str, str]:
    raw = value.strip()
    if raw.startswith("gs://"):
        parsed = urlparse(raw)
        bucket = _bucket_name(parsed.netloc)
        key = parsed.path.lstrip("/")
    else:
        bucket = _bucket_name(default_bucket)
        key = raw.lstrip("/")
    if not key or any(part == ".." for part in Path(key).parts):
        raise ValueError(f"invalid GCS object path: {value!r}")
    return bucket, key


_default_store: ModelStore | None = None


def get_store() -> ModelStore:
    """Module-level singleton — built lazily on first call."""
    global _default_store
    if _default_store is None:
        _default_store = ModelStore()
    return _default_store
