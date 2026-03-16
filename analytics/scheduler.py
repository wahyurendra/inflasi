"""
ETL Scheduler — MVP cron menggunakan APScheduler.

Jadwal:
  06:00 WIB  — Global datasets (kurs, energy, FAO, commodity, news)
  10:30 WIB  — PIHPS BI (update pagi)
  13:30 WIB  — PIHPS BI (update siang)
  14:00 WIB  — BMKG Weather
  17:30 WIB  — Analytics (risk scores, alerts, insights, anomaly, forecast)
"""

import asyncio
import logging
import os
import ssl
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

_project_root = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(_project_root, ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("scheduler")

# Resolve database URL
_raw_url = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL", "")
if _raw_url.startswith("postgresql://"):
    DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _raw_url.startswith("postgresql+asyncpg://"):
    DATABASE_URL = _raw_url
else:
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"


def _create_engine(url: str):
    kwargs = {"pool_size": 5, "max_overflow": 10, "pool_recycle": 300}
    if "supabase" in url:
        ssl_ctx = ssl.create_default_context()
        kwargs["connect_args"] = {"ssl": ssl_ctx}
        url = url.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")
    return create_async_engine(url, **kwargs)


async def run_pihps_job(session_factory: async_sessionmaker):
    """Run PIHPS BI pipeline for today."""
    logger.info("Starting PIHPS BI pipeline")
    async with session_factory() as db:
        from app.etl.pipelines.pihps_bi import PIHPSPipeline
        pipeline = PIHPSPipeline(db=db, target_date=date.today())
        result = await pipeline.run()
        logger.info(f"PIHPS result: {result}")


async def run_bmkg_job(session_factory: async_sessionmaker):
    """Run BMKG weather pipeline."""
    logger.info("Starting BMKG weather pipeline")
    async with session_factory() as db:
        from app.etl.pipelines.bmkg_weather import BMKGWeatherPipeline
        pipeline = BMKGWeatherPipeline(db=db, target_date=date.today())
        result = await pipeline.run()
        logger.info(f"BMKG result: {result}")


async def run_global_job(session_factory: async_sessionmaker):
    """Run all global dataset pipelines."""
    logger.info("Starting global pipelines")
    async with session_factory() as db:
        from app.etl.pipelines.exchange_rate import ExchangeRatePipeline
        from app.etl.pipelines.energy_price import EnergyPricePipeline
        from app.etl.pipelines.fao_food_price import FAOFoodPricePipeline
        from app.etl.pipelines.commodity_global import CommodityGlobalPipeline
        from app.etl.pipelines.gdelt_news import GDELTNewsPipeline

        pipelines = [
            ExchangeRatePipeline(db=db, start_date=date.today(), end_date=date.today()),
            EnergyPricePipeline(db=db, days=7),
            FAOFoodPricePipeline(db=db),
            CommodityGlobalPipeline(db=db, year_start=2024),
            GDELTNewsPipeline(db=db, days=1),
        ]

        for pipeline in pipelines:
            try:
                result = await pipeline.run()
                logger.info(f"{pipeline.name}: {result}")
            except Exception as e:
                logger.error(f"{pipeline.name} failed: {e}")


async def run_analytics_job(session_factory: async_sessionmaker):
    """Run all analytics calculations."""
    logger.info("Starting analytics calculations")
    today = date.today()

    async with session_factory() as db:
        # 1. Risk scores
        from app.services.risk_scorer import RiskScorer
        scorer = RiskScorer(db)
        await scorer.calculate_all_scores(today)
        logger.info("Risk scores calculated")

        # 2. Alerts
        from app.services.alert_engine import AlertEngine
        engine = AlertEngine(db)
        alert_count = await engine.run_daily(today)
        logger.info(f"Generated {alert_count} alerts")

        # 3. Anomaly detection
        from app.services.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector(db)
        anomaly_count = await detector.detect_anomalies(today)
        logger.info(f"Detected {anomaly_count} anomalies")

        # 4. Forecast (runs weekly or on-demand for performance)
        # Uncomment below to run daily forecast:
        # from app.services.forecast_engine import ForecastEngine
        # forecaster = ForecastEngine(db)
        # forecast_count = await forecaster.forecast_all(horizon_days=14)
        # logger.info(f"Generated {forecast_count} forecasts")

        # 5. Insights
        from app.services.insight_generator import InsightGenerator
        generator = InsightGenerator(db)
        await generator.generate_daily(today)
        logger.info("Daily insight generated")


async def main():
    """Start the scheduler with APScheduler."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error("APScheduler not installed. Install with: pip install apscheduler")
        logger.info("Falling back to one-shot mode: running all jobs now")
        await run_all_once()
        return

    engine = _create_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")

    # Global datasets — 06:00 WIB
    scheduler.add_job(
        run_global_job, CronTrigger(hour=6, minute=0),
        args=[session_factory], id="global", name="Global Datasets"
    )

    # PIHPS BI — 10:30 WIB
    scheduler.add_job(
        run_pihps_job, CronTrigger(hour=10, minute=30),
        args=[session_factory], id="pihps_am", name="PIHPS Pagi"
    )

    # PIHPS BI — 13:30 WIB
    scheduler.add_job(
        run_pihps_job, CronTrigger(hour=13, minute=30),
        args=[session_factory], id="pihps_pm", name="PIHPS Siang"
    )

    # BMKG Weather — 14:00 WIB
    scheduler.add_job(
        run_bmkg_job, CronTrigger(hour=14, minute=0),
        args=[session_factory], id="bmkg", name="BMKG Weather"
    )

    # Analytics — 17:30 WIB
    scheduler.add_job(
        run_analytics_job, CronTrigger(hour=17, minute=30),
        args=[session_factory], id="analytics", name="Analytics"
    )

    scheduler.start()
    logger.info("Scheduler started. Jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.name}: {job.trigger}")

    # Keep running forever
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


async def run_all_once():
    """Run all jobs once (for cron or manual execution)."""
    engine = _create_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    await run_global_job(session_factory)
    await run_pihps_job(session_factory)
    await run_bmkg_job(session_factory)
    await run_analytics_job(session_factory)

    await engine.dispose()
    logger.info("All jobs completed")


if __name__ == "__main__":
    asyncio.run(main())
