"""Background validation pipeline for crowdsourced price reports.

Consumes report ids from the `stream:price_reports` Redis Stream, scores each report
against the recent regional median, sets its status + confidence, notifies the
reporter, and emits the result to `stream:validation_done`. Runs in-process in the
api-gateway lifespan — Redis Streams (with consumer groups + acks) replace Kafka.

Degrades gracefully: if Redis is unavailable the loop retries; reports are still
created (the create endpoint publishes best-effort) and can be reviewed manually.
"""

import asyncio
import logging
import statistics
from datetime import date, timedelta
from decimal import Decimal

import cuid2
import httpx
from sqlalchemy import select

from app.config import settings
from app.core.redis import get_redis
from app.database import async_session
from app.models.tables import FactPriceDaily, Notification, PriceReport

logger = logging.getLogger("validation_pipeline")

STREAM_REPORTS = "stream:price_reports"
STREAM_DONE = "stream:validation_done"
GROUP = "validation_workers"

# Deviation (%) from the regional 7-day median.
APPROVE_MAX_DEV = 25.0   # within ±25% -> auto-approve
FLAG_MIN_DEV = 50.0      # beyond ±50% -> flag for human review


class ValidationPipeline:
    def __init__(self) -> None:
        self._task: "asyncio.Task | None" = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        redis = get_redis()
        try:
            await redis.xgroup_create(STREAM_REPORTS, GROUP, id="0", mkstream=True)
        except Exception:
            pass  # consumer group already exists
        self._stop.clear()
        self._task = asyncio.create_task(self._loop())
        logger.info("ValidationPipeline started")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ValidationPipeline stopped")

    async def _loop(self) -> None:
        redis = get_redis()
        consumer = f"validator-{id(self)}"
        while not self._stop.is_set():
            try:
                resp = await redis.xreadgroup(GROUP, consumer, {STREAM_REPORTS: ">"}, count=10, block=5000)
                for _stream, entries in resp or []:
                    for msg_id, data in entries:
                        try:
                            await self._validate(data.get("report_id"))
                        except Exception:
                            logger.exception("validation failed for %s", data)
                        finally:
                            await redis.xack(STREAM_REPORTS, GROUP, msg_id)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("consume loop error; retrying")
                await asyncio.sleep(5)

    async def _validate(self, report_id: "str | None") -> None:
        if not report_id:
            return
        async with async_session() as db:
            report = (await db.execute(select(PriceReport).where(PriceReport.id == report_id))).scalar()
            if report is None:
                return

            prices = await self._regional_prices(db, report.commodity_id, report.region_id)
            if not prices:
                confidence, status, deviation = 50.0, "PENDING", None
            else:
                median = statistics.median(prices)
                deviation = round((float(report.harga) - median) / median * 100, 2) if median else None
                confidence = round(max(0.0, 100.0 - abs(deviation)), 2) if deviation is not None else 50.0
                if deviation is None:
                    status = "PENDING"
                elif abs(deviation) <= APPROVE_MAX_DEV:
                    status = "APPROVED"
                elif abs(deviation) >= FLAG_MIN_DEV:
                    status = "FLAGGED"
                else:
                    status = "PENDING"

                # Cross-check with the ML gateway: if it flags an anomaly the simple band
                # missed, don't auto-approve — route to human review instead.
                if status == "APPROVED":
                    ml = await self._ml_anomaly(prices, float(report.harga))
                    if ml and ml.get("is_anomaly"):
                        status = "PENDING"

            report.confidence_score = Decimal(str(confidence))
            report.status = status
            db.add(self._notification(report, status, deviation))
            await db.commit()

        await get_redis().xadd(
            STREAM_DONE,
            {"report_id": report_id, "status": status, "confidence": str(confidence)},
        )
        logger.info("validated report %s -> %s (confidence %.1f)", report_id, status, confidence)

    @staticmethod
    async def _regional_prices(db, commodity_id: int, region_id: int, days: int = 30) -> "list[float]":
        since = date.today() - timedelta(days=days)
        res = await db.execute(
            select(FactPriceDaily.harga).where(
                FactPriceDaily.commodity_id == commodity_id,
                FactPriceDaily.region_id == region_id,
                FactPriceDaily.tanggal >= since,
            )
        )
        return [float(h) for (h,) in res.all() if h is not None]

    @staticmethod
    async def _ml_anomaly(history: "list[float]", value: float) -> "dict | None":
        # Graceful: any failure (ml-gateway down/timeout) -> None -> ignored.
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.post(
                    f"{settings.ml_gateway_url}/anomaly/detect",
                    json={"history": history, "value": value},
                )
                r.raise_for_status()
                return r.json()
        except Exception:
            return None

    @staticmethod
    def _notification(report: PriceReport, status: str, deviation: "float | None") -> Notification:
        if status == "APPROVED":
            title, message = "Laporan disetujui", "Laporan harga Anda lolos validasi otomatis. Terima kasih!"
        elif status == "FLAGGED":
            title, message = "Laporan ditandai", "Harga yang dilaporkan jauh dari rata-rata wilayah dan akan ditinjau petugas."
        else:
            title, message = "Laporan diterima", "Laporan Anda sedang menunggu tinjauan petugas."
        return Notification(
            id=cuid2.cuid_wrapper(),
            user_id=report.user_id,
            type="report_validation",
            title=title,
            message=message,
            data={"reportId": report.id, "status": status, "deviation": deviation},
        )
