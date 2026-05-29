"""Build `feature_store_monthly` rows from raw fact tables.

The builder is intentionally SQL-heavy. We pull every period × region pair in
the requested window, then assemble the columns in a single transaction:

* `fact_inflation_monthly` provides the CPI core (ihk, mtm/yoy/ytd) and the
  future-target lookups for M+1, M+3, M+6.
* `fact_price_daily` aggregates into the food-price proxy (overall index +
  per-commodity MoM for the strategic six).
* `fact_climate` averages to a regional monthly rainfall/temperature snapshot.
* `fact_macro_driver` provides kurs + BBM (national, joined as-of period start).
* `dim_calendar` flags ramadan/lebaran/idul_adha/nataru/harvest by stamping
  any-day-in-month booleans.

Targets are computed by joining the same `fact_inflation_monthly` table at
period + N months. When the future row doesn't exist yet (the most-recent
months) the target stays NULL — that's expected and the training pipeline
filters it out via `split`.

Splits: train = all but the trailing 12 months, validation = months [-12, -6),
test = months [-6, 0). Tune by editing `_assign_split`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("monthly_feature_builder")

STRATEGIC_COMMODITIES = {
    "beras": ("beras",),
    "cabai_merah": ("cabai_merah", "cabai_merah_keriting", "cabai_merah_besar"),
    "bawang_merah": ("bawang_merah",),
    "telur": ("telur_ayam_ras", "telur"),
    "ayam": ("daging_ayam_ras", "ayam_ras"),
    "minyak_goreng": ("minyak_goreng_curah", "minyak_goreng_kemasan", "minyak_goreng"),
}

_TARGET_HORIZONS = (1, 3, 6)


@dataclass
class BuildSummary:
    rows_written: int
    rows_skipped: int
    periods: list[str]


class MonthlyFeatureBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build(
        self,
        *,
        start: date | None = None,
        end: date | None = None,
        region_ids: list[int] | None = None,
        target_type: str = "inflation",
    ) -> BuildSummary:
        """Upsert feature rows for every (period, region) pair in the window.

        `start`/`end` default to the full CPI history present in
        `fact_inflation_monthly`. When `region_ids` is given, only those
        regions are built (cheap reruns after a fix).
        """
        periods_regions = await self._periods_regions(
            start=start, end=end, region_ids=region_ids,
        )
        if not periods_regions:
            logger.info("monthly builder: no candidate (period, region) pairs")
            return BuildSummary(rows_written=0, rows_skipped=0, periods=[])

        rows_written = 0
        rows_skipped = 0
        touched_periods: set[date] = set()

        for period, region_id, level_wilayah in periods_regions:
            try:
                row = await self._build_row(
                    period=period,
                    region_id=region_id,
                    level_wilayah=level_wilayah,
                    target_type=target_type,
                )
                if row is None:
                    rows_skipped += 1
                    continue
                await self._upsert(row)
                rows_written += 1
                touched_periods.add(period)
            except Exception:
                logger.exception(
                    "monthly builder: failed for period=%s region=%s",
                    period, region_id,
                )
                rows_skipped += 1

        await self.db.commit()
        return BuildSummary(
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            periods=sorted(p.isoformat() for p in touched_periods),
        )

    # ── Discovery ─────────────────────────────────────────────

    async def _periods_regions(
        self,
        *,
        start: date | None,
        end: date | None,
        region_ids: list[int] | None,
    ) -> list[tuple[date, int, str | None]]:
        clauses: list[str] = ["fim.kelompok IS NULL OR fim.kelompok = 'umum'"]
        params: dict[str, Any] = {}
        if start:
            clauses.append("fim.periode >= :start"); params["start"] = start
        if end:
            clauses.append("fim.periode <= :end"); params["end"] = end
        if region_ids:
            clauses.append("fim.region_id = ANY(:region_ids)")
            params["region_ids"] = region_ids

        where = " AND ".join(f"({c})" for c in clauses)
        rows = (await self.db.execute(
            text(f"""
                SELECT DISTINCT fim.periode, fim.region_id, fim.level_wilayah
                FROM fact_inflation_monthly fim
                WHERE {where}
                ORDER BY fim.periode, fim.region_id
            """),
            params,
        )).fetchall()
        return [
            (r.periode, int(r.region_id), r.level_wilayah)
            for r in rows
        ]

    # ── Row assembly ──────────────────────────────────────────

    async def _build_row(
        self,
        *,
        period: date,
        region_id: int,
        level_wilayah: str | None,
        target_type: str,
    ) -> dict[str, Any] | None:
        inflation = await self._inflation_lookup(period, region_id)
        if inflation is None:
            return None

        lags = await self._inflation_lags(period, region_id)
        rolling = await self._inflation_rolling(period, region_id)
        food = await self._food_price_aggregate(period, region_id)
        per_commodity = await self._per_commodity_change(period, region_id)
        climate = await self._climate_aggregate(period, region_id)
        macro = await self._macro_lookup(period)
        flags = await self._calendar_flags(period)
        targets = await self._targets(period, region_id)
        split = _assign_split(period)
        dq = _quality_score(inflation, food, climate, macro)

        return {
            "period": period,
            "region_id": region_id,
            "target_type": target_type,
            "level_wilayah": level_wilayah,
            **inflation,
            **lags,
            **rolling,
            **food,
            **per_commodity,
            **climate,
            **macro,
            **flags,
            **targets,
            "data_quality_score": dq,
            "split": split,
        }

    async def _inflation_lookup(
        self, period: date, region_id: int,
    ) -> dict[str, Any] | None:
        row = (await self.db.execute(
            text("""
                SELECT ihk, inflasi_mtm, inflasi_yoy, inflasi_ytd
                FROM fact_inflation_monthly
                WHERE periode = :period AND region_id = :region_id
                  AND (kelompok IS NULL OR kelompok = 'umum')
                ORDER BY ihk NULLS LAST
                LIMIT 1
            """),
            {"period": period, "region_id": region_id},
        )).first()
        if row is None:
            return None
        return {
            "ihk": row.ihk,
            "inflasi_mtm": row.inflasi_mtm,
            "inflasi_yoy": row.inflasi_yoy,
            "inflasi_ytd": row.inflasi_ytd,
        }

    async def _inflation_lags(
        self, period: date, region_id: int,
    ) -> dict[str, Any]:
        rows = (await self.db.execute(
            text("""
                SELECT periode, inflasi_mtm
                FROM fact_inflation_monthly
                WHERE region_id = :region_id
                  AND (kelompok IS NULL OR kelompok = 'umum')
                  AND periode IN (
                    (:period::date - INTERVAL '1 month')::date,
                    (:period::date - INTERVAL '3 months')::date,
                    (:period::date - INTERVAL '6 months')::date,
                    (:period::date - INTERVAL '12 months')::date
                  )
            """),
            {"period": period, "region_id": region_id},
        )).fetchall()
        by_period = {r.periode: r.inflasi_mtm for r in rows}
        return {
            "inflasi_lag_1": by_period.get(_shift_months(period, -1)),
            "inflasi_lag_3": by_period.get(_shift_months(period, -3)),
            "inflasi_lag_6": by_period.get(_shift_months(period, -6)),
            "inflasi_lag_12": by_period.get(_shift_months(period, -12)),
        }

    async def _inflation_rolling(
        self, period: date, region_id: int,
    ) -> dict[str, Any]:
        row = (await self.db.execute(
            text("""
                SELECT
                  AVG(CASE WHEN periode > (:period::date - INTERVAL '3 months') THEN inflasi_mtm END) AS roll3,
                  AVG(CASE WHEN periode > (:period::date - INTERVAL '6 months') THEN inflasi_mtm END) AS roll6,
                  STDDEV_SAMP(CASE WHEN periode > (:period::date - INTERVAL '3 months') THEN inflasi_mtm END) AS std3,
                  STDDEV_SAMP(CASE WHEN periode > (:period::date - INTERVAL '6 months') THEN inflasi_mtm END) AS std6
                FROM fact_inflation_monthly
                WHERE region_id = :region_id
                  AND (kelompok IS NULL OR kelompok = 'umum')
                  AND periode < :period
            """),
            {"period": period, "region_id": region_id},
        )).first()
        return {
            "inflasi_rolling_3": row.roll3 if row else None,
            "inflasi_rolling_6": row.roll6 if row else None,
            "inflasi_std_3": row.std3 if row else None,
            "inflasi_std_6": row.std6 if row else None,
        }

    async def _food_price_aggregate(
        self, period: date, region_id: int,
    ) -> dict[str, Any]:
        # Mean of monthly mean per commodity → coarse food-price index;
        # MoM change relative to previous month, anomaly = mean - 6m baseline.
        row = (await self.db.execute(
            text("""
                WITH cur AS (
                  SELECT AVG(harga::float) AS avg_now
                  FROM fact_price_daily
                  WHERE region_id = :region_id
                    AND date_trunc('month', tanggal) = :period
                ),
                prev AS (
                  SELECT AVG(harga::float) AS avg_prev
                  FROM fact_price_daily
                  WHERE region_id = :region_id
                    AND date_trunc('month', tanggal) = (:period::date - INTERVAL '1 month')::date
                ),
                base AS (
                  SELECT AVG(harga::float) AS avg_base
                  FROM fact_price_daily
                  WHERE region_id = :region_id
                    AND tanggal BETWEEN (:period::date - INTERVAL '6 months')::date
                                    AND (:period::date - INTERVAL '1 day')::date
                )
                SELECT cur.avg_now, prev.avg_prev, base.avg_base
                FROM cur, prev, base
            """),
            {"period": period, "region_id": region_id},
        )).first()
        if row is None:
            return {
                "food_price_index": None,
                "food_price_change_mom": None,
                "food_price_anomaly": None,
            }
        avg_now = row.avg_now
        avg_prev = row.avg_prev
        avg_base = row.avg_base
        return {
            "food_price_index": avg_now,
            "food_price_change_mom": _pct_change(avg_prev, avg_now),
            "food_price_anomaly": _pct_change(avg_base, avg_now),
        }

    async def _per_commodity_change(
        self, period: date, region_id: int,
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for slot, kodes in STRATEGIC_COMMODITIES.items():
            row = (await self.db.execute(
                text("""
                    WITH ids AS (
                        SELECT id FROM dim_commodity WHERE kode_komoditas = ANY(:kodes)
                    ),
                    cur AS (
                        SELECT AVG(harga::float) AS avg_now
                        FROM fact_price_daily
                        WHERE region_id = :region_id
                          AND commodity_id IN (SELECT id FROM ids)
                          AND date_trunc('month', tanggal) = :period
                    ),
                    prev AS (
                        SELECT AVG(harga::float) AS avg_prev
                        FROM fact_price_daily
                        WHERE region_id = :region_id
                          AND commodity_id IN (SELECT id FROM ids)
                          AND date_trunc('month', tanggal) = (:period::date - INTERVAL '1 month')::date
                    )
                    SELECT cur.avg_now, prev.avg_prev FROM cur, prev
                """),
                {"period": period, "region_id": region_id, "kodes": list(kodes)},
            )).first()
            out[f"{slot}_change_mom"] = (
                _pct_change(row.avg_prev, row.avg_now) if row else None
            )
        return out

    async def _climate_aggregate(
        self, period: date, region_id: int,
    ) -> dict[str, Any]:
        row = (await self.db.execute(
            text("""
                WITH cur AS (
                  SELECT AVG(curah_hujan::float) AS rain_now,
                         AVG(suhu_rata::float) AS temp_now,
                         SUM(CASE WHEN warning_level IN ('SIAGA','AWAS') THEN 1 ELSE 0 END) AS extreme
                  FROM fact_climate
                  WHERE region_id = :region_id
                    AND date_trunc('month', tanggal) = :period
                ),
                base AS (
                  SELECT AVG(curah_hujan::float) AS rain_base
                  FROM fact_climate
                  WHERE region_id = :region_id
                    AND tanggal BETWEEN (:period::date - INTERVAL '12 months')::date
                                    AND (:period::date - INTERVAL '1 day')::date
                )
                SELECT cur.rain_now, cur.temp_now, cur.extreme, base.rain_base
                FROM cur, base
            """),
            {"period": period, "region_id": region_id},
        )).first()
        if row is None:
            return {
                "rainfall_mean": None, "rainfall_anomaly": None,
                "temperature_mean": None, "extreme_weather_days": None,
            }
        return {
            "rainfall_mean": row.rain_now,
            "rainfall_anomaly": _pct_change(row.rain_base, row.rain_now),
            "temperature_mean": row.temp_now,
            "extreme_weather_days": row.extreme,
        }

    async def _macro_lookup(self, period: date) -> dict[str, Any]:
        row = (await self.db.execute(
            text("""
                WITH cur AS (
                  SELECT AVG(kurs_usd_idr::float) AS k, AVG(harga_bbm::float) AS b
                  FROM fact_macro_driver
                  WHERE date_trunc('month', tanggal) = :period
                ),
                prev AS (
                  SELECT AVG(kurs_usd_idr::float) AS k_prev, AVG(harga_bbm::float) AS b_prev
                  FROM fact_macro_driver
                  WHERE date_trunc('month', tanggal) = (:period::date - INTERVAL '1 month')::date
                )
                SELECT cur.k, cur.b, prev.k_prev, prev.b_prev FROM cur, prev
            """),
            {"period": period},
        )).first()
        if row is None:
            return {
                "kurs_usd_idr": None, "kurs_change_mom": None,
                "bbm_price": None, "bbm_change_mom": None,
            }
        return {
            "kurs_usd_idr": row.k,
            "kurs_change_mom": _pct_change(row.k_prev, row.k),
            "bbm_price": row.b,
            "bbm_change_mom": _pct_change(row.b_prev, row.b),
        }

    async def _calendar_flags(self, period: date) -> dict[str, Any]:
        row = (await self.db.execute(
            text("""
                SELECT
                  MAX(CASE WHEN ramadan_flag THEN 1 ELSE 0 END)::int AS ramadan,
                  MAX(CASE WHEN lebaran_minus_7 OR lebaran_plus_7 OR lebaran_minus_14 THEN 1 ELSE 0 END)::int AS lebaran,
                  MAX(CASE WHEN idul_adha_window THEN 1 ELSE 0 END)::int AS idul,
                  MAX(CASE WHEN nataru_minus_14 THEN 1 ELSE 0 END)::int AS nataru,
                  MAX(CASE WHEN harvest_flag THEN 1 ELSE 0 END)::int AS harvest
                FROM dim_calendar
                WHERE date_trunc('month', tanggal) = :period
            """),
            {"period": period},
        )).first()
        return {
            "month": period.month,
            "quarter": (period.month - 1) // 3 + 1,
            "ramadan_flag": row.ramadan if row else 0,
            "lebaran_flag": row.lebaran if row else 0,
            "idul_adha_flag": row.idul if row else 0,
            "nataru_flag": row.nataru if row else 0,
            "harvest_flag": row.harvest if row else 0,
        }

    async def _targets(self, period: date, region_id: int) -> dict[str, Any]:
        rows = (await self.db.execute(
            text("""
                SELECT periode, inflasi_mtm
                FROM fact_inflation_monthly
                WHERE region_id = :region_id
                  AND (kelompok IS NULL OR kelompok = 'umum')
                  AND periode IN (
                    (:period::date + INTERVAL '1 month')::date,
                    (:period::date + INTERVAL '3 months')::date,
                    (:period::date + INTERVAL '6 months')::date
                  )
            """),
            {"period": period, "region_id": region_id},
        )).fetchall()
        by_period = {r.periode: r.inflasi_mtm for r in rows}
        return {
            f"target_inflation_m{h}": by_period.get(_shift_months(period, h))
            for h in _TARGET_HORIZONS
        }

    # ── Persistence ───────────────────────────────────────────

    async def _upsert(self, row: dict[str, Any]) -> None:
        cols = list(row.keys())
        placeholders = ", ".join(f":{c}" for c in cols)
        col_list = ", ".join(cols)
        update_cols = ", ".join(
            f"{c} = EXCLUDED.{c}" for c in cols
            if c not in {"period", "region_id", "target_type"}
        )
        sql = f"""
            INSERT INTO feature_store_monthly ({col_list})
            VALUES ({placeholders})
            ON CONFLICT (period, region_id, target_type)
            DO UPDATE SET {update_cols}, updated_at = NOW()
        """
        await self.db.execute(text(sql), row)


# ── Helpers ──────────────────────────────────────────────────

def _shift_months(d: date, months: int) -> date:
    """Return the first day of `d`'s month, offset by `months`. Negative goes back."""
    month_index = d.year * 12 + (d.month - 1) + months
    year, month0 = divmod(month_index, 12)
    return date(year, month0 + 1, 1)


def _pct_change(prev: Any, cur: Any) -> float | None:
    try:
        p = float(prev) if prev is not None else None
        c = float(cur) if cur is not None else None
    except (TypeError, ValueError):
        return None
    if p is None or c is None or p == 0:
        return None
    return round((c - p) / p * 100, 4)


def _assign_split(period: date) -> str:
    """Time-based split. Anchored at today; the trailing 12 months become val/test."""
    today = date.today()
    months_back = (today.year - period.year) * 12 + (today.month - period.month)
    if months_back > 12:
        return "train"
    if months_back > 6:
        return "validation"
    return "test"


def _quality_score(*blocks: dict[str, Any]) -> Decimal:
    """Fraction of non-null columns across the input blocks. Lazy but useful."""
    total = 0
    present = 0
    for block in blocks:
        for v in block.values():
            total += 1
            if v is not None:
                present += 1
    if total == 0:
        return Decimal("0")
    return Decimal(str(round(present / total, 4)))
