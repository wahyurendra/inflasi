"""One-shot analytics batch — risk scores, alerts, anomaly, forecast, insights.

Extracted from scheduler.py's run_analytics_job so it can run as a k8s CronJob
(`python run_analytics.py`) on the api-gateway image, instead of the in-process
APScheduler daemon. Idempotent per day; safe to re-run.

Usage:
  python run_analytics.py              # today
  python run_analytics.py 2026-05-27   # a specific date
"""

import asyncio
import logging
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("analytics")


def _resolve_url() -> tuple[str, dict]:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL", "")
    if raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not raw:
        raw = "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"
    connect_args: dict = {}
    return raw, connect_args


async def run_analytics(session_factory: async_sessionmaker, target: date) -> None:
    async with session_factory() as db:
        from app.services.risk_scorer import RiskScorer
        await RiskScorer(db).calculate_all_scores(target)
        logger.info("Risk scores calculated")

        from app.services.feature_builder import FeatureBuilder
        feature_rows = await FeatureBuilder(db).build(target)
        logger.info("Materialized %s feature_store_daily rows", feature_rows)

        from app.services.alert_engine import AlertEngine
        alert_count = await AlertEngine(db).run_daily(target)
        logger.info("Generated %s alerts", alert_count)

        from app.services.anomaly_detector import AnomalyDetector
        anomaly_count = await AnomalyDetector(db).detect_anomalies(target)
        logger.info("Detected %s anomalies", anomaly_count)

        from app.services.forecast_engine import ForecastEngine
        forecast_count = await ForecastEngine(db).forecast_all(horizon_days=14)
        logger.info("Generated %s forecasts", forecast_count)

        from app.services.insight_generator import InsightGenerator
        await InsightGenerator(db).generate("harian", target)
        logger.info("Daily insight generated")

        # Auto-generated public blog article. Isolated so an LLM/API hiccup
        # never fails the analytics batch.
        try:
            from app.services.blog_generator import BlogGenerator
            post = await BlogGenerator(db).generate(target)
            logger.info("Daily blog post generated: %s (%s)", post["slug"], post["model"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Blog generation failed (non-fatal): %s", exc)


async def main() -> None:
    target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    url, connect_args = _resolve_url()
    engine = create_async_engine(url, connect_args=connect_args, pool_recycle=300)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("Running analytics batch for %s", target)
    try:
        await run_analytics(session_factory, target)
    finally:
        await engine.dispose()
    logger.info("Analytics batch complete")


if __name__ == "__main__":
    asyncio.run(main())
