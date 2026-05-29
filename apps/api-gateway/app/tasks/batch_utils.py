"""Helpers shared by batch tasks: pair discovery, chunking, error capture.

Kept separate from the orchestrators so unit tests can target the pure helpers
without spinning up DB/Redis. Two responsibilities only:

* `discover_active_pairs` — pull (commodity_id, region_id) seen in the recent
  fact_price_daily window. Fresh pairs auto-qualify; stale pairs drop off.
* `chunk` + `BatchError` — boilerplate every orchestrator otherwise re-invents.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Iterator, TypeVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")


@dataclass
class BatchError:
    """One pair-level failure inside a batch run. Captured so the orchestrator
    can keep running other pairs and report aggregated counts at the end."""
    commodity_id: int
    region_id: int
    horizon: int | None
    error: str


async def discover_active_pairs(
    db: AsyncSession,
    *,
    window_days: int = 7,
) -> list[tuple[int, int]]:
    """Return distinct (commodity_id, region_id) pairs touched in the last N days.

    Mirrors the heuristic already used by `PredictionService.forecast_all`: a pair
    is "active" iff we have fresh fact rows for it. New commodities/regions
    automatically join the rotation once their first row lands.
    """
    rows = (await db.execute(
        text("""
            SELECT DISTINCT commodity_id, region_id
            FROM fact_price_daily
            WHERE tanggal >= :since
            ORDER BY commodity_id, region_id
        """),
        {"since": date.today() - timedelta(days=window_days)},
    )).fetchall()
    return [(int(r.commodity_id), int(r.region_id)) for r in rows]


def chunk(items: Iterable[T], size: int) -> Iterator[list[T]]:
    """Yield successive chunks of `items` of at most `size` elements."""
    buf: list[T] = []
    for x in items:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf
