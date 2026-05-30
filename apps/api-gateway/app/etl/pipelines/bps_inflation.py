"""Pipeline: BPS Inflation Monthly

Sumber: BPS Web API (https://webapi.bps.go.id)
Frekuensi: Bulanan (BPS publishes around the 1st–3rd of each month for the
prior month)
Data: IHK + Inflasi MtM + Inflasi YoY per provinsi (umum kelompok).

API layout (v1):

    GET https://webapi.bps.go.id/v1/api/list/
        model/data/lang/ind/domain/{domain}/var/{var}/key/{api_key}/

* `domain` = BPS region code, "0000" for national or the 4-digit province
  code (e.g. "1100" for Aceh). The 2-digit codes in `dim_region.kode_wilayah`
  are extended with "00" suffix to match.
* `var` = the variable id; the constants below cover IHK + inflation MtM + YoY.

Response shape (relevant fields):

    {
      "status": "OK",
      "data": [...meta], [{ "val": 105.32, "var": 2088, "tahun": 2024, "turtahun": 5, ... }]
    }

`turtahun` is the period derivative; for monthly variables it's the month
index (1..12). We fold those back into `period = first day of month`.

Without an `BPS_API_KEY` env var the pipeline degrades gracefully: it logs a
warning, records nothing, and exits with `records=0`. This keeps the CronJob
green on fresh environments while still flagging missing config.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import date
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

BPS_BASE_URL = "https://webapi.bps.go.id/v1/api/list"

# var_id for monthly CPI / inflation series. These map to the umum (overall)
# basket; the kelompok-level breakdown uses a different domain table that
# can be added later when the analytics surfaces need it.
BPS_VARS: dict[str, str] = {
    "2088": "ihk",
    "2089": "inflasi_mtm",
    "2090": "inflasi_yoy",
    "2092": "inflasi_ytd",
}

# Map dim_region.kode_wilayah (2-digit) → BPS domain code (4-digit, "00" suffix
# for province roll-up). Hardcoded so we don't introduce a runtime dependency
# on dim_region availability.
BPS_DOMAIN_MAP: dict[str, str] = {
    "00": "0000",
    "11": "1100", "12": "1200", "13": "1300", "14": "1400", "15": "1500",
    "16": "1600", "17": "1700", "18": "1800", "19": "1900", "21": "2100",
    "31": "3100", "32": "3200", "33": "3300", "34": "3400", "35": "3500",
    "36": "3600",
    "51": "5100", "52": "5200", "53": "5300",
    "61": "6100", "62": "6200", "63": "6300", "64": "6400", "65": "6500",
    "71": "7100", "72": "7200", "73": "7300", "74": "7400", "75": "7500", "76": "7600",
    "81": "8100", "82": "8200",
    "91": "9100", "92": "9200",
}


class BPSInflationPipeline:
    """Pull monthly CPI + inflation indicators from BPS Web API.

    Single entry point: `run()`. Fetches all regions / vars within
    `[start_year, end_year]`, upserts each (period, region, var) into
    `fact_inflation_monthly`, and returns the number of rows written.
    """

    name = "bps_inflation"

    def __init__(
        self,
        db: AsyncSession,
        *,
        api_key: str | None = None,
        start_year: int = 2022,
        end_year: int | None = None,
        region_codes: list[str] | None = None,
        per_call_delay_s: float = 0.25,
    ):
        self.db = db
        self.api_key = api_key or os.getenv("BPS_API_KEY") or ""
        self.start_year = start_year
        self.end_year = end_year or date.today().year
        self.region_codes = region_codes or sorted(BPS_DOMAIN_MAP.keys())
        self.per_call_delay_s = per_call_delay_s
        # Cloudflare blocks the default httpx UA on webapi.bps.go.id; mimic a
        # real browser. follow_redirects covers periodic host moves.
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "Accept": "application/json, text/plain, */*",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": "https://webapi.bps.go.id/",
            },
        )

    async def run(self) -> int:
        if not self.api_key:
            logger.warning(
                "[%s] BPS_API_KEY not set; skipping. Register a free key at "
                "https://webapi.bps.go.id and export BPS_API_KEY.",
                self.name,
            )
            return 0

        region_ids = await self._region_id_map()
        if not region_ids:
            logger.warning("[%s] dim_region empty; seed dimensions first.", self.name)
            return 0

        total = 0
        try:
            for region_code in self.region_codes:
                domain = BPS_DOMAIN_MAP.get(region_code)
                region_id = region_ids.get(region_code)
                if domain is None or region_id is None:
                    logger.debug(
                        "[%s] skipping region_code=%s (no domain / region_id)",
                        self.name, region_code,
                    )
                    continue
                rows = await self._fetch_region(region_code, domain)
                if not rows:
                    continue
                written = await self._upsert(rows, region_id=region_id)
                total += written
        finally:
            await self.client.aclose()

        logger.info("[%s] wrote %s fact_inflation_monthly rows", self.name, total)
        return total

    # ── HTTP ──────────────────────────────────────────────────

    async def _fetch_region(
        self, region_code: str, domain: str,
    ) -> dict[tuple[date, str], dict[str, Any]]:
        """Pull every var for this region; collapse per (period, region) into one row.

        Returns a mapping keyed by `(period, "umum")` with one column per BPS
        metric. The "umum" sentinel matches `fact_inflation_monthly.kelompok`
        semantics — we explicitly avoid kelompok breakdowns in this v1.
        """
        merged: dict[tuple[date, str], dict[str, Any]] = {}

        for var_id, column in BPS_VARS.items():
            try:
                payload = await self._fetch_var(domain=domain, var_id=var_id)
            except Exception:
                logger.exception(
                    "[%s] failed region=%s var=%s", self.name, region_code, var_id,
                )
                continue
            for row in _parse_payload(payload, year_min=self.start_year, year_max=self.end_year):
                key = (row["period"], "umum")
                merged.setdefault(key, {"period": row["period"], "kelompok": "umum"})[column] = row["value"]
            await asyncio.sleep(self.per_call_delay_s)

        return merged

    async def _fetch_var(self, *, domain: str, var_id: str) -> dict[str, Any]:
        url = (
            f"{BPS_BASE_URL}/model/data/lang/ind/"
            f"domain/{domain}/var/{var_id}/key/{self.api_key}/"
        )
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    # ── Persistence ───────────────────────────────────────────

    async def _upsert(
        self,
        rows_by_key: dict[tuple[date, str], dict[str, Any]],
        *,
        region_id: int,
    ) -> int:
        if not rows_by_key:
            return 0
        params = [
            {
                "periode": values["period"],
                "region_id": region_id,
                "level_wilayah": "nasional" if region_id else "provinsi",
                "ihk": values.get("ihk"),
                "inflasi_mtm": values.get("inflasi_mtm"),
                "inflasi_yoy": values.get("inflasi_yoy"),
                "inflasi_ytd": values.get("inflasi_ytd"),
                "kelompok": values.get("kelompok") or "umum",
            }
            for values in rows_by_key.values()
        ]
        await self.db.execute(
            text("""
                INSERT INTO fact_inflation_monthly
                  (periode, region_id, level_wilayah, ihk, inflasi_mtm,
                   inflasi_yoy, inflasi_ytd, kelompok, sumber)
                VALUES
                  (:periode, :region_id, :level_wilayah, :ihk, :inflasi_mtm,
                   :inflasi_yoy, :inflasi_ytd, :kelompok, 'BPS')
                ON CONFLICT (periode, region_id, kelompok, commodity_id)
                DO UPDATE SET
                  ihk = COALESCE(EXCLUDED.ihk, fact_inflation_monthly.ihk),
                  inflasi_mtm = COALESCE(EXCLUDED.inflasi_mtm, fact_inflation_monthly.inflasi_mtm),
                  inflasi_yoy = COALESCE(EXCLUDED.inflasi_yoy, fact_inflation_monthly.inflasi_yoy),
                  inflasi_ytd = COALESCE(EXCLUDED.inflasi_ytd, fact_inflation_monthly.inflasi_ytd),
                  updated_at = NOW()
            """),
            params,
        )
        await self.db.commit()
        return len(params)

    async def _region_id_map(self) -> dict[str, int]:
        rows = (await self.db.execute(
            text("SELECT id, kode_wilayah FROM dim_region")
        )).fetchall()
        return {r.kode_wilayah: int(r.id) for r in rows}


def _parse_payload(
    payload: dict[str, Any], *, year_min: int, year_max: int,
) -> list[dict[str, Any]]:
    """Flatten BPS v1 list-API output to `[{period, value}]`.

    Schema notes (from observed responses):
    * `payload["data"]` is a 2-element list. `data[0]` is metadata; `data[1]`
      is the value series.
    * Each series row exposes `val`, `tahun` (year), `turtahun` (month, 1..12),
      and an `id` whose suffix is `"YYYY{TT}"`. We prefer the explicit
      `tahun`/`turtahun` fields and fall back to parsing `id` when those are
      missing.
    """
    if not isinstance(payload, dict):
        return []
    data = payload.get("data") or []
    if not isinstance(data, list) or len(data) < 2:
        return []
    series = data[1]
    if not isinstance(series, list):
        return []

    out: list[dict[str, Any]] = []
    for row in series:
        if not isinstance(row, dict):
            continue
        value = row.get("val")
        if value is None:
            continue
        year, month = _resolve_year_month(row)
        if year is None or month is None:
            continue
        if not (year_min <= year <= year_max):
            continue
        if not (1 <= month <= 12):
            continue
        try:
            out.append({"period": date(year, month, 1), "value": float(value)})
        except (TypeError, ValueError):
            continue
    return out


def _resolve_year_month(row: dict[str, Any]) -> tuple[int | None, int | None]:
    year = row.get("tahun") or row.get("year")
    month = row.get("turtahun") or row.get("turvar")

    try:
        year_i = int(year) if year is not None else None
    except (TypeError, ValueError):
        year_i = None
    try:
        month_i = int(month) if month is not None else None
    except (TypeError, ValueError):
        month_i = None

    if year_i and month_i:
        return year_i, month_i

    raw_id = row.get("id") or row.get("val_id") or ""
    s = str(raw_id)
    if len(s) >= 6 and s[-6:].isdigit():
        y = int(s[-6:-2])
        m = int(s[-2:])
        if 1900 < y < 2100 and 1 <= m <= 12:
            return y, m
    return year_i, month_i
