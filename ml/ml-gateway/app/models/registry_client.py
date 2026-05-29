"""HTTP client for the api-gateway's internal model registry endpoint.

Looks up which artifact path is currently ``is_active = true`` for a given
``(model_type, target_type, horizon)`` slot so the loaders can fetch the right
file from MinIO.

Failures (api-gateway down, no active model) return ``None`` — the caller is
expected to skip that model and the ensemble degrades gracefully.

Cache: lookups are TTL-cached (default 60s) so we don't hammer the registry on
every prediction. Bust the cache via :meth:`clear` after a promotion.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("registry_client")

_DEFAULT_TTL = 60.0


@dataclass
class ActiveModelRef:
    id: int
    model_name: str
    model_type: str
    target_type: str
    horizon: int | None
    version: str
    artifact_path: str


class RegistryClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        ttl_seconds: float = _DEFAULT_TTL,
        timeout: float = 5.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("API_GATEWAY_URL", "http://inflasi-api:8080")).rstrip("/")
        self.ttl = ttl_seconds
        self.timeout = timeout
        self._cache: dict[tuple[str, str, int | None], tuple[float, ActiveModelRef | None]] = {}
        self._lock = threading.Lock()

    def get_active(
        self,
        *,
        model_type: str,
        target_type: str = "price",
        horizon: int | None = None,
    ) -> ActiveModelRef | None:
        key = (model_type, target_type, horizon)
        now = time.time()
        with self._lock:
            entry = self._cache.get(key)
            if entry and (now - entry[0]) < self.ttl:
                return entry[1]

        ref = self._fetch(model_type=model_type, target_type=target_type, horizon=horizon)
        with self._lock:
            self._cache[key] = (now, ref)
        return ref

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    # ── Internals ────────────────────────────────────────────

    def _fetch(
        self,
        *,
        model_type: str,
        target_type: str,
        horizon: int | None,
    ) -> ActiveModelRef | None:
        url = f"{self.base_url}/api/internal/models/active"
        params: dict[str, Any] = {"model_type": model_type, "target_type": target_type}
        if horizon is not None:
            params["horizon"] = horizon
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            return ActiveModelRef(
                id=int(data["id"]),
                model_name=data["model_name"],
                model_type=data["model_type"],
                target_type=data["target_type"],
                horizon=data.get("horizon"),
                version=data["version"],
                artifact_path=data["artifact_path"],
            )
        except httpx.HTTPError:
            logger.warning("registry lookup failed for %s/%s/h=%s", model_type, target_type, horizon)
            return None
        except Exception:
            logger.exception("registry lookup unexpected error")
            return None


_default_client: RegistryClient | None = None


def get_registry_client() -> RegistryClient:
    global _default_client
    if _default_client is None:
        _default_client = RegistryClient()
    return _default_client
