"""Map a free-text `price_reports.nama_pasar` to a `dim_market.id`.

The crowd-report form takes a typed name like "Pasar Senen" or "pasar senen
jakpus". We need to attach that to a stable dimension row so analytics and
dashboards can group by physical market.

Strategy (cheap → expensive):

1. **Normalized exact match** in the region: case-fold + collapse whitespace,
   compare against `dim_market.nama_pasar` (the index on `LOWER(nama_pasar)`
   makes this cheap).
2. **Fuzzy match** using `difflib.SequenceMatcher` over candidates in the same
   region. The threshold is conservative (≥ 0.85) — false positives are worse
   than NULL here.
3. **Auto-create** when a strong-looking name appears repeatedly in
   `price_reports` but doesn't match anything yet. The MVP only does steps 1+2;
   the auto-create step is opt-in via `auto_create=True` so we don't fill the
   dimension with low-confidence rows by accident.

Returns either a `dim_market.id` or `None`. Callers should treat `None` as
"keep the raw `nama_pasar` string" — the original column stays populated.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.market_repo import MarketRepo
from app.models.tables import DimMarket

logger = logging.getLogger("market_normalizer")

_FUZZY_THRESHOLD = 0.85
_PREFIX_NOISE = re.compile(r"^(?:pasar|psr|toko)\s+", re.IGNORECASE)


@dataclass
class MarketMatch:
    market_id: int
    nama_pasar: str
    score: float
    method: str  # "exact" | "fuzzy" | "created"


def _normalize(name: str) -> str:
    """Lower-case, strip the common "Pasar"/"Psr" prefix, collapse whitespace."""
    s = (name or "").strip().lower()
    s = _PREFIX_NOISE.sub("", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


class MarketNormalizer:
    """Stateful per-request normalizer — caches the region's market list once."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MarketRepo(db)
        self._cache: dict[int, list[DimMarket]] = {}

    async def resolve(
        self,
        *,
        region_id: int,
        nama_pasar: str,
        auto_create: bool = False,
    ) -> MarketMatch | None:
        """Look up `nama_pasar` inside `region_id`; optionally create on miss."""
        raw = (nama_pasar or "").strip()
        if not raw:
            return None

        exact = await self.repo.find_by_region_name(
            region_id=region_id, nama_pasar=raw,
        )
        if exact:
            return MarketMatch(
                market_id=exact.id, nama_pasar=exact.nama_pasar,
                score=1.0, method="exact",
            )

        target = _normalize(raw)
        if not target:
            return None

        candidates = await self._candidates(region_id)
        best_id: int | None = None
        best_name = ""
        best_score = 0.0
        for c in candidates:
            score = SequenceMatcher(None, target, _normalize(c.nama_pasar)).ratio()
            if score > best_score:
                best_score = score
                best_id = c.id
                best_name = c.nama_pasar

        if best_id is not None and best_score >= _FUZZY_THRESHOLD:
            logger.debug(
                "fuzzy match: %r -> %r (score=%.3f)", raw, best_name, best_score,
            )
            return MarketMatch(
                market_id=best_id, nama_pasar=best_name,
                score=round(best_score, 4), method="fuzzy",
            )

        if auto_create:
            row = await self.repo.upsert(region_id=region_id, nama_pasar=raw)
            self._cache.pop(region_id, None)  # invalidate cached list
            return MarketMatch(
                market_id=row.id, nama_pasar=row.nama_pasar,
                score=1.0, method="created",
            )
        return None

    async def _candidates(self, region_id: int) -> list[DimMarket]:
        if region_id not in self._cache:
            self._cache[region_id] = await self.repo.list_by_region(
                region_id, active_only=True,
            )
        return self._cache[region_id]
