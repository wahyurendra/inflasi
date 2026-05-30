"""Materialize `feature_store_daily` rows from raw tables.

Reads `fact_price_daily` + `dim_calendar` + `fact_climate` + `fact_macro_driver`
+ `ext_exchange_rate` + `fact_inflation_monthly`, computes lags / rolling stats /
quality flags / supervised targets (h7, h14, h30), upserts into
`feature_store_daily`.

Grain: one row per (date, commodity_kode, region_kode, entity_level, series_family).
For MVP we materialize at province level only — series_family='daily_province'.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.feature_encoder import CODE_COLUMNS, encode_codes

logger = logging.getLogger(__name__)

_LOOKBACK_DAYS = 60   # extra history fetched so lags/rolling are populated
_HORIZONS = (7, 14, 30)


class FeatureBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Public API ────────────────────────────────────────────

    async def build(
        self,
        target_date: date,
        lookback_days: int = _LOOKBACK_DAYS,
        *,
        commodity_kodes: list[str] | None = None,
        region_kodes: list[str] | None = None,
    ) -> int:
        """Materialize features for [target_date - lookback, target_date].

        When ``commodity_kodes`` / ``region_kodes`` are provided, the build is
        scoped to those pairs only (used by the refresh worker for incremental
        per-pair refresh after a crowd report is APPROVED). The daily CronJob
        leaves both ``None`` to materialize everything.
        """
        start = target_date - timedelta(days=lookback_days)
        return await self._materialize(
            start, target_date,
            commodity_kodes=commodity_kodes, region_kodes=region_kodes,
        )

    async def backfill(
        self,
        start: date,
        end: date,
        *,
        commodity_kodes: list[str] | None = None,
        region_kodes: list[str] | None = None,
    ) -> int:
        """Bulk materialize [start, end] (inclusive)."""
        if end < start:
            raise ValueError("end must be >= start")
        return await self._materialize(
            start, end,
            commodity_kodes=commodity_kodes, region_kodes=region_kodes,
        )

    # ── Pipeline ──────────────────────────────────────────────

    async def _materialize(
        self,
        start: date,
        end: date,
        *,
        commodity_kodes: list[str] | None = None,
        region_kodes: list[str] | None = None,
    ) -> int:
        # Fetch with extra prior window so lags/rolling are accurate at `start`.
        fetch_start = start - timedelta(days=_LOOKBACK_DAYS)
        # Need future window to compute targets at `end`.
        fetch_end = end + timedelta(days=max(_HORIZONS))

        prices_df = await self._load_prices(
            fetch_start, fetch_end,
            commodity_kodes=commodity_kodes, region_kodes=region_kodes,
        )
        if prices_df.empty:
            logger.warning("No prices in [%s, %s]; skipping", fetch_start, fetch_end)
            return 0

        calendar_df = await self._load_calendar(fetch_start, fetch_end)
        weather_df = await self._load_weather(
            fetch_start, fetch_end, region_kodes=region_kodes,
        )
        macro_df = await self._load_macro(fetch_start, fetch_end)
        inflation_df = await self._load_inflation(fetch_start, fetch_end)

        groups: list[pd.DataFrame] = []
        for _, grp in prices_df.groupby(["commodity_kode", "region_kode"], sort=False):
            groups.append(self._build_group(grp))

        if not groups:
            return 0

        feat = pd.concat(groups, ignore_index=True)

        # Restrict to the requested window (we needed extras for lag/rolling/targets).
        feat = feat[(feat["date"] >= start) & (feat["date"] <= end)]
        if feat.empty:
            return 0

        # Join calendar / weather / macro / inflation (broadcast by date / region+date).
        feat = self._join_calendar(feat, calendar_df)
        feat = self._join_weather(feat, weather_df)
        feat = self._join_macro(feat, macro_df, inflation_df)
        feat = self._assign_split(feat)
        feat = self._fill_metadata(feat)

        # Add the *_code columns the training pipeline expects. Done after metadata
        # so commodity_id / region_id / entity_level / unit / series_family are all
        # set. Shared with ml/training/ via `feature_encoder.encode_codes`.
        feat = encode_codes(feat)

        records = self._to_records(feat)
        await self._upsert(records)
        await self.db.commit()
        logger.info("Materialized %s feature rows [%s, %s]", len(records), start, end)
        return len(records)

    # ── Loaders ───────────────────────────────────────────────

    async def _load_prices(
        self,
        start: date,
        end: date,
        *,
        commodity_kodes: list[str] | None = None,
        region_kodes: list[str] | None = None,
    ) -> pd.DataFrame:
        """Load joined prices + dim codes."""
        where = ["fp.tanggal BETWEEN :start AND :end"]
        params: dict = {"start": start, "end": end}
        if commodity_kodes:
            where.append("dc.kode_komoditas = ANY(:ck)")
            params["ck"] = list(commodity_kodes)
        if region_kodes:
            where.append("dr.kode_wilayah = ANY(:rk)")
            params["rk"] = list(region_kodes)
        sql = f"""
            SELECT fp.tanggal AS date,
                   fp.harga::float AS price,
                   fp.sumber AS sumber,
                   dc.kode_komoditas AS commodity_kode,
                   dc.nama_display AS commodity_name,
                   dc.satuan AS unit,
                   dr.kode_wilayah AS region_kode,
                   dr.nama_provinsi AS region_name,
                   dr.level_wilayah AS entity_level
            FROM fact_price_daily fp
            JOIN dim_commodity dc ON dc.id = fp.commodity_id
            JOIN dim_region dr ON dr.id = fp.region_id
            WHERE {" AND ".join(where)}
            ORDER BY fp.tanggal
        """
        rows = (await self.db.execute(text(sql), params)).mappings().all()
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    async def _load_calendar(self, start: date, end: date) -> pd.DataFrame:
        rows = (await self.db.execute(
            text("""
                SELECT tanggal AS date, day_of_week, week_of_year, quarter,
                       is_weekend, is_month_start, is_month_end,
                       ramadan_flag, lebaran_minus_21, lebaran_minus_14,
                       lebaran_minus_7, lebaran_plus_7, nataru_minus_14,
                       idul_adha_window, school_holiday_flag, harvest_flag,
                       bulan AS month
                FROM dim_calendar
                WHERE tanggal BETWEEN :start AND :end
            """),
            {"start": start, "end": end},
        )).mappings().all()
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    async def _load_weather(
        self,
        start: date,
        end: date,
        *,
        region_kodes: list[str] | None = None,
    ) -> pd.DataFrame:
        where = ["fc.tanggal BETWEEN :start AND :end"]
        params: dict = {"start": start, "end": end}
        if region_kodes:
            where.append("dr.kode_wilayah = ANY(:rk)")
            params["rk"] = list(region_kodes)
        sql = f"""
            SELECT fc.tanggal AS date,
                   dr.kode_wilayah AS region_kode,
                   AVG(fc.curah_hujan)::float AS rainfall_1d,
                   AVG(fc.suhu_rata)::float AS temperature_avg,
                   COUNT(*) AS weather_station_count,
                   SUM(CASE WHEN fc.warning_level IN ('SIAGA','AWAS','EKSTREM') THEN 1 ELSE 0 END) AS extreme_count
            FROM fact_climate fc
            JOIN dim_region dr ON dr.id = fc.region_id
            WHERE {" AND ".join(where)}
            GROUP BY fc.tanggal, dr.kode_wilayah
        """
        rows = (await self.db.execute(text(sql), params)).mappings().all()
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["extreme_weather_flag"] = (df["extreme_count"].astype(int) > 0).astype(int)
        df = df.drop(columns=["extreme_count"])
        # Rainfall anomaly = deviation from 30-day mean per region.
        df = df.sort_values(["region_kode", "date"]).reset_index(drop=True)
        df["rainfall_anomaly"] = (
            df.groupby("region_kode")["rainfall_1d"]
            .transform(lambda s: s - s.rolling(30, min_periods=5).mean())
        )
        return df

    async def _load_macro(self, start: date, end: date) -> pd.DataFrame:
        rows = (await self.db.execute(
            text("""
                SELECT er.tanggal AS date,
                       er.change_pct::float AS usd_idr_change,
                       fm.harga_bbm::float AS harga_bbm
                FROM ext_exchange_rate er
                LEFT JOIN fact_macro_driver fm ON fm.tanggal = er.tanggal
                WHERE er.tanggal BETWEEN :start AND :end
            """),
            {"start": start, "end": end},
        )).mappings().all()
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # fuel_price_flag: 1 when fuel price changed vs previous record.
        df = df.sort_values("date").reset_index(drop=True)
        df["fuel_price_flag"] = (df["harga_bbm"].diff().fillna(0) != 0).astype(int)
        # bi_rate is not yet sourced — leave None; downstream tolerates.
        df["bi_rate"] = np.nan
        df = df.drop(columns=["harga_bbm"])
        return df

    async def _load_inflation(self, start: date, end: date) -> pd.DataFrame:
        """Monthly inflation (national, kelompok IS NULL) broadcast to daily."""
        rows = (await self.db.execute(
            text("""
                SELECT periode AS month_start,
                       inflasi_mtm::float AS inflation_mom,
                       inflasi_yoy::float AS inflation_yoy
                FROM fact_inflation_monthly
                WHERE kelompok IS NULL
                  AND periode BETWEEN :start AND :end
                ORDER BY periode
            """),
            {"start": start - timedelta(days=60), "end": end},
        )).mappings().all()
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["month_start"] = pd.to_datetime(df["month_start"]).dt.date
        # Lag-1 month: shift down by 1 row (since rows are monthly, ascending).
        df["inflation_mom_lag_1"] = df["inflation_mom"].shift(1)
        df["inflation_yoy_lag_1"] = df["inflation_yoy"].shift(1)
        return df[["month_start", "inflation_mom_lag_1", "inflation_yoy_lag_1"]]

    # ── Per-group feature engineering ─────────────────────────

    def _build_group(self, g: pd.DataFrame) -> pd.DataFrame:
        # Densify daily index so lags/rolling are consistent.
        g = g.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
        if g.empty:
            return g
        date_range = pd.date_range(g["date"].min(), g["date"].max(), freq="D").date
        g = g.set_index("date").reindex(date_range)
        g.index.name = "date"
        g = g.reset_index()

        # Forward-fill metadata.
        for col in ["commodity_kode", "commodity_name", "unit", "region_kode", "region_name", "entity_level", "sumber"]:
            g[col] = g[col].ffill().bfill()

        # Imputation tracking.
        original_price = g["price"].copy()
        g["is_imputed"] = original_price.isna() & g["price"].ffill().notna()
        g["price"] = g["price"].ffill()
        g["valid_price_flag"] = (g["price"].notna() & (g["price"] > 0)).astype(int)

        # Lags.
        for n in (1, 3, 7, 14, 30):
            g[f"price_lag_{n}"] = g["price"].shift(n)

        # Rolling windows.
        r7 = g["price"].rolling(7, min_periods=1)
        r14 = g["price"].rolling(14, min_periods=1)
        r30 = g["price"].rolling(30, min_periods=1)
        g["rolling_mean_7"] = r7.mean()
        g["rolling_mean_14"] = r14.mean()
        g["rolling_mean_30"] = r30.mean()
        g["rolling_std_7"] = g["price"].rolling(7, min_periods=2).std()
        g["rolling_min_7"] = r7.min()
        g["rolling_max_7"] = r7.max()
        g["rolling_median_7"] = r7.median()
        g["rolling_median_30"] = r30.median()

        # Changes / pct_changes.
        g["price_change_1d"] = g["price"].diff(1)
        g["price_change_7d"] = g["price"].diff(7)
        g["price_change_30d"] = g["price"].diff(30)
        g["pct_change_1d"] = g["price"].pct_change(1)
        g["pct_change_7d"] = g["price"].pct_change(7)
        g["pct_change_30d"] = g["price"].pct_change(30)

        # Quality windows.
        miss_mask = original_price.isna().astype(int)
        g["missing_rate_30d"] = miss_mask.rolling(30, min_periods=1).mean()
        g["is_imputed_count_30d"] = g["is_imputed"].astype(int).rolling(30, min_periods=1).sum()
        g["data_quality_score"] = (1 - g["missing_rate_30d"]) * 100
        g["missing_rate"] = g["missing_rate_30d"]
        g["missing_gap_length"] = _max_gap(original_price)
        g["source_count"] = (g["sumber"].notna()).astype(int)
        g["status"] = np.where(g["valid_price_flag"] == 1, "trainable", "unobserved")

        # Anomaly candidate via 30d z-score.
        mu = r30.mean()
        sd = g["price"].rolling(30, min_periods=5).std()
        z = (g["price"] - mu) / sd.replace(0, np.nan)
        g["anomaly_candidate"] = z.abs() > 3

        # Targets — shift backwards (future price at +h days).
        for h in _HORIZONS:
            g[f"target_h{h}"] = g["price"].shift(-h)

        return g

    # ── Joins ─────────────────────────────────────────────────

    def _join_calendar(self, feat: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
        if cal.empty:
            # Fallback: derive from date.
            d = pd.to_datetime(feat["date"])
            feat["day_of_week"] = d.dt.dayofweek
            feat["week_of_year"] = d.dt.isocalendar().week.astype(int)
            feat["month"] = d.dt.month
            feat["quarter"] = d.dt.quarter
            feat["is_weekend"] = (d.dt.dayofweek >= 5).astype(int)
            feat["is_month_start"] = d.dt.is_month_start.astype(int)
            feat["is_month_end"] = d.dt.is_month_end.astype(int)
            for col in ("ramadan_flag", "lebaran_minus_21", "lebaran_minus_14",
                        "lebaran_minus_7", "lebaran_plus_7", "nataru_minus_14",
                        "idul_adha_window", "school_holiday_flag", "harvest_flag"):
                feat[col] = 0
            return feat
        return feat.merge(cal, on="date", how="left")

    def _join_weather(self, feat: pd.DataFrame, w: pd.DataFrame) -> pd.DataFrame:
        if w.empty:
            for col in ("rainfall_1d", "temperature_avg", "weather_station_count",
                        "rainfall_anomaly", "extreme_weather_flag"):
                feat[col] = np.nan
            feat["has_weather"] = 0
            return feat
        merged = feat.merge(w, on=["date", "region_kode"], how="left")
        merged["has_weather"] = merged["rainfall_1d"].notna().astype(int)
        return merged

    def _join_macro(self, feat: pd.DataFrame, macro: pd.DataFrame, infl: pd.DataFrame) -> pd.DataFrame:
        if macro.empty:
            for col in ("usd_idr_change", "bi_rate", "fuel_price_flag"):
                feat[col] = np.nan if col != "fuel_price_flag" else 0
            feat["has_macro"] = 0
        else:
            feat = feat.merge(macro, on="date", how="left")
            feat["has_macro"] = feat["usd_idr_change"].notna().astype(int)

        if infl.empty:
            feat["inflation_mom_lag_1"] = np.nan
            feat["inflation_yoy_lag_1"] = np.nan
            return feat

        # Broadcast monthly inflation to daily.
        feat["_month_start"] = pd.to_datetime(feat["date"]).dt.to_period("M").dt.to_timestamp().dt.date
        feat = feat.merge(infl, left_on="_month_start", right_on="month_start", how="left")
        feat = feat.drop(columns=["_month_start", "month_start"], errors="ignore")
        return feat

    def _assign_split(self, feat: pd.DataFrame) -> pd.DataFrame:
        today = date.today()
        cutoff_val = today - timedelta(days=60)
        cutoff_test = today - timedelta(days=30)

        def _split(d: date) -> str:
            if d <= cutoff_val:
                return "train"
            if d <= cutoff_test:
                return "val"
            return "test"

        feat["split"] = feat["date"].apply(_split)
        feat["row_role"] = feat["target_h30"].apply(
            lambda v: "supervised_h30_plus" if pd.notna(v) else "predict_only"
        )
        return feat

    def _fill_metadata(self, feat: pd.DataFrame) -> pd.DataFrame:
        feat["entity_id"] = feat["region_kode"]
        feat["entity_name"] = feat["region_name"]
        feat["frequency"] = "daily"
        # series_family by entity level: daily_province | daily_kabupaten | daily_national
        feat["series_family"] = feat["entity_level"].apply(
            lambda lv: {
                "provinsi": "daily_province",
                "kab_kota": "daily_kabupaten",
                "nasional": "daily_national",
            }.get(lv, "daily_other")
        )
        feat["entity_level"] = feat["entity_level"].apply(
            lambda lv: {
                "provinsi": "province",
                "kab_kota": "kabupaten",
                "nasional": "national",
            }.get(lv, lv)
        )
        # Promote the natural-grain kode columns to the id names the encoder and
        # DB schema use (feature_store_daily stores the kode string as
        # commodity_id / region_id). Done here — after the joins above which key
        # on *_kode — so encode_codes() and _to_records() see commodity_id /
        # region_id directly. Keeps the serving path identical to the training
        # parquet (no train/serve skew).
        feat = feat.rename(columns={"commodity_kode": "commodity_id", "region_kode": "region_id"})
        return feat

    # ── Upsert ────────────────────────────────────────────────

    def _to_records(self, feat: pd.DataFrame) -> list[dict]:
        # Map dataframe columns → DB columns.
        rename = {
            "commodity_kode": "commodity_id",
            "region_kode": "region_id",
        }
        out = feat.rename(columns=rename)

        # Drop any helper columns that aren't in DB schema.
        wanted = _DB_COLUMNS
        for col in wanted:
            if col not in out.columns:
                out[col] = None
        out = out[wanted]

        # Numpy/pandas NaN → None for SQL.
        records = out.replace({np.nan: None}).to_dict(orient="records")
        # Booleans coming from pandas may be numpy.bool_ — normalize.
        for r in records:
            for k, v in list(r.items()):
                if isinstance(v, (np.bool_, np.integer, np.floating)):
                    r[k] = v.item()
                elif pd.isna(v) if v is not None else False:
                    r[k] = None
        return records

    async def _upsert(self, records: list[dict]) -> None:
        if not records:
            return
        # Chunk to avoid huge parameter packs.
        for i in range(0, len(records), 500):
            chunk = records[i:i + 500]
            await self.db.execute(_UPSERT_SQL, chunk)


def _max_gap(series: pd.Series) -> pd.Series:
    """Length of the longest NaN run ending at each index (0 if not NaN)."""
    is_na = series.isna().astype(int)
    # Reset count on non-NaN.
    out = is_na.groupby((is_na == 0).cumsum()).cumsum()
    return out


_DB_COLUMNS = [
    "date", "commodity_id", "region_id", "entity_level", "series_family",
    "split", "row_role", "commodity_name", "region_name", "entity_id", "entity_name",
    "frequency", "price", "unit", "valid_price_flag", "is_imputed",
    "missing_gap_length", "anomaly_candidate", "data_quality_score", "missing_rate",
    "status", "source_count",
    "day_of_week", "week_of_year", "month", "quarter",
    "is_weekend", "is_month_start", "is_month_end",
    "price_lag_1", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_30", "rolling_std_7",
    "rolling_min_7", "rolling_max_7", "rolling_median_7", "rolling_median_30",
    "price_change_1d", "price_change_7d", "price_change_30d",
    "pct_change_1d", "pct_change_7d", "pct_change_30d",
    "missing_rate_30d", "is_imputed_count_30d",
    "ramadan_flag", "lebaran_minus_21", "lebaran_minus_14", "lebaran_minus_7",
    "lebaran_plus_7", "nataru_minus_14", "idul_adha_window",
    "school_holiday_flag", "harvest_flag",
    "rainfall_1d", "temperature_avg", "weather_station_count",
    "rainfall_anomaly", "extreme_weather_flag",
    "inflation_mom_lag_1", "inflation_yoy_lag_1", "usd_idr_change",
    "bi_rate", "fuel_price_flag",
    "target_h7", "target_h14", "target_h30",
    "has_weather", "has_macro",
    # *_code columns from feature_encoder.encode_codes (training/inference alignment).
    *CODE_COLUMNS,
]


_PLACEHOLDERS = ", ".join(f":{c}" for c in _DB_COLUMNS)
_UPDATE_SET = ", ".join(f"{c} = EXCLUDED.{c}" for c in _DB_COLUMNS if c not in {
    "date", "commodity_id", "region_id", "entity_level", "series_family",
})
_UPSERT_SQL = text(f"""
INSERT INTO feature_store_daily ({", ".join(_DB_COLUMNS)})
VALUES ({_PLACEHOLDERS})
ON CONFLICT (date, commodity_id, region_id, entity_level, series_family)
DO UPDATE SET {_UPDATE_SET}, updated_at = NOW()
""")
