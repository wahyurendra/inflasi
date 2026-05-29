"""Evaluate stored forecasts against the latest actuals.

Runs after the daily price ETL settles. Persists per-(model_version, horizon)
metrics rows into `forecast_backtest_results` so the dashboard can chart the
quality trend over time.

K8s schedule: every night at 11:00 WIB (16:00 UTC) — well after the analytics
CronJob has refreshed `fact_price_daily` and `analytics_forecast`.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import asdict

from app.database import async_session
from app.services.forecast_monitor import ForecastMonitor

logger = logging.getLogger("evaluate_forecasts")


async def run(*, window_days: int = 30, target_type: str = "price") -> list[dict]:
    async with async_session() as db:
        monitor = ForecastMonitor(db)
        out = await monitor.evaluate_window(
            window_days=window_days, target_type=target_type,
        )
    logger.info(
        "forecast evaluation: %s slots evaluated over last %s days",
        len(out), window_days,
    )
    return [asdict(m) for m in out]


def _main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate stored forecasts against actuals.")
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--target-type", default="price")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run(window_days=args.window_days, target_type=args.target_type))


if __name__ == "__main__":
    _main()
