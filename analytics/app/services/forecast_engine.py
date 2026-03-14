"""
Price Forecast Engine menggunakan Prophet.

Memprediksi harga komoditas H+7 dan H+14 berdasarkan:
- Harga historis 90+ hari
- Seasonality (Ramadan, Nataru, panen)
- Holidays dari dim_calendar
- Optional: curah hujan sebagai regressor
"""

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

MODEL_VERSION = "prophet-v1"


class ForecastEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def forecast_commodity(
        self,
        commodity_id: int,
        region_id: int,
        horizon_days: int = 14,
        history_days: int = 90,
    ) -> list[dict]:
        """Generate price forecast for a single commodity-region pair."""
        # 1. Get historical price data
        end_date = date.today()
        start_date = end_date - timedelta(days=history_days)

        result = await self.db.execute(
            text("""
                SELECT tanggal, harga
                FROM fact_price_daily
                WHERE commodity_id = :cid AND region_id = :rid
                  AND tanggal BETWEEN :start AND :end
                ORDER BY tanggal
            """),
            {"cid": commodity_id, "rid": region_id, "start": start_date, "end": end_date},
        )
        rows = result.fetchall()

        if len(rows) < 30:
            logger.warning(
                f"Not enough data for forecast: commodity={commodity_id}, "
                f"region={region_id}, rows={len(rows)}"
            )
            return []

        # 2. Get holidays from dim_calendar
        result = await self.db.execute(
            text("""
                SELECT tanggal, nama_libur, musim
                FROM dim_calendar
                WHERE is_hari_libur = TRUE
                  AND tanggal BETWEEN :start AND :future
            """),
            {"start": start_date, "end": end_date,
             "future": end_date + timedelta(days=horizon_days)},
        )
        holidays_rows = result.fetchall()

        # 3. Run Prophet forecast
        try:
            from prophet import Prophet
            import pandas as pd

            df = pd.DataFrame(
                [{"ds": row.tanggal, "y": float(row.harga)} for row in rows]
            )
            df["ds"] = pd.to_datetime(df["ds"])

            # Build holidays dataframe
            holidays_df = None
            if holidays_rows:
                holidays_df = pd.DataFrame([
                    {"holiday": row.nama_libur or row.musim or "holiday",
                     "ds": pd.Timestamp(row.tanggal),
                     "lower_window": 0,
                     "upper_window": 1}
                    for row in holidays_rows
                    if row.nama_libur or row.musim
                ])

            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                holidays=holidays_df,
                changepoint_prior_scale=0.05,
                interval_width=0.80,
            )

            model.fit(df)

            future = model.make_future_dataframe(periods=horizon_days, freq="D")
            forecast = model.predict(future)

            # Only return future dates
            future_forecast = forecast[forecast["ds"] > pd.Timestamp(end_date)]

            predictions = []
            for _, row in future_forecast.iterrows():
                predictions.append({
                    "tanggal": row["ds"].date(),
                    "yhat": round(float(row["yhat"]), 2),
                    "yhat_lower": round(float(row["yhat_lower"]), 2),
                    "yhat_upper": round(float(row["yhat_upper"]), 2),
                })

            return predictions

        except ImportError:
            logger.warning("Prophet not installed, using simple linear fallback")
            return self._simple_forecast(rows, horizon_days)

    def _simple_forecast(self, rows: list, horizon_days: int) -> list[dict]:
        """Fallback: simple moving average + trend forecast when Prophet unavailable."""
        import statistics

        prices = [float(r.harga) for r in rows]
        last_date = rows[-1].tanggal

        # Calculate trend from last 14 days
        recent = prices[-14:] if len(prices) >= 14 else prices
        if len(recent) >= 2:
            daily_change = (recent[-1] - recent[0]) / len(recent)
        else:
            daily_change = 0

        # Calculate volatility for confidence interval
        try:
            std = statistics.stdev(recent)
        except statistics.StatisticsError:
            std = 0

        predictions = []
        last_price = prices[-1]
        for i in range(1, horizon_days + 1):
            forecast_date = last_date + timedelta(days=i)
            yhat = last_price + daily_change * i
            predictions.append({
                "tanggal": forecast_date,
                "yhat": round(yhat, 2),
                "yhat_lower": round(yhat - 1.5 * std, 2),
                "yhat_upper": round(yhat + 1.5 * std, 2),
            })

        return predictions

    async def forecast_all(self, horizon_days: int = 14) -> int:
        """Run forecast for all active commodity-region pairs and store results."""
        # Get all commodity-region combinations with recent data
        result = await self.db.execute(
            text("""
                SELECT DISTINCT commodity_id, region_id
                FROM fact_price_daily
                WHERE tanggal >= :recent
            """),
            {"recent": date.today() - timedelta(days=7)},
        )
        pairs = result.fetchall()

        count = 0
        for pair in pairs:
            predictions = await self.forecast_commodity(
                pair.commodity_id, pair.region_id, horizon_days
            )
            if predictions:
                await self._store_forecasts(
                    pair.commodity_id, pair.region_id, horizon_days, predictions
                )
                count += len(predictions)

        await self.db.commit()
        logger.info(f"Generated {count} forecast records for {len(pairs)} pairs")
        return count

    async def _store_forecasts(
        self, commodity_id: int, region_id: int, horizon: int, predictions: list[dict]
    ) -> None:
        for pred in predictions:
            await self.db.execute(
                text("""
                    INSERT INTO analytics_forecast
                        (tanggal, region_id, commodity_id, horizon, yhat, yhat_lower, yhat_upper, model_version)
                    VALUES
                        (:tanggal, :region_id, :commodity_id, :horizon, :yhat, :yhat_lower, :yhat_upper, :model_version)
                    ON CONFLICT (tanggal, region_id, commodity_id, horizon)
                    DO UPDATE SET
                        yhat = EXCLUDED.yhat,
                        yhat_lower = EXCLUDED.yhat_lower,
                        yhat_upper = EXCLUDED.yhat_upper,
                        model_version = EXCLUDED.model_version
                """),
                {
                    "tanggal": pred["tanggal"],
                    "region_id": region_id,
                    "commodity_id": commodity_id,
                    "horizon": horizon,
                    "yhat": pred["yhat"],
                    "yhat_lower": pred["yhat_lower"],
                    "yhat_upper": pred["yhat_upper"],
                    "model_version": MODEL_VERSION,
                },
            )

    async def get_forecast(
        self, commodity_id: int, region_id: int, horizon: int = 14
    ) -> list[dict]:
        """Get stored forecast data."""
        result = await self.db.execute(
            text("""
                SELECT tanggal, yhat, yhat_lower, yhat_upper, model_version
                FROM analytics_forecast
                WHERE commodity_id = :cid AND region_id = :rid AND horizon = :horizon
                  AND tanggal >= CURRENT_DATE
                ORDER BY tanggal
            """),
            {"cid": commodity_id, "rid": region_id, "horizon": horizon},
        )
        return [dict(row._mapping) for row in result.fetchall()]
