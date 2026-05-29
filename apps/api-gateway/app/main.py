import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import router as api_router
from app.core.redis import close_redis
from app.workers.refresh_worker import RefreshWorker
from app.workers.validation_pipeline import ValidationPipeline

logger = logging.getLogger("inflasi-api")

DESCRIPTION = """
## INFLASI Analytics API

Backend analytics engine untuk platform pemantauan inflasi pangan Indonesia.

### Fitur Utama

- **Analytics** — Kalkulasi perubahan harga, volatilitas, dan risk score
- **Alerts** — Deteksi anomali harga dan sistem peringatan dini
- **Insights** — Ringkasan analitik harian dan mingguan
- **Forecast** — Prediksi harga komoditas menggunakan Prophet
- **Drivers** — Analisis faktor penggerak inflasi

### Data Sources

| Sumber | Deskripsi |
|--------|-----------|
| PIHPS BI | Harga pangan harian dari Bank Indonesia |
| BPS | Data inflasi resmi Badan Pusat Statistik |
| BMKG | Data cuaca dan iklim |
| EIA | Harga energi global (minyak, gas) |
"""

tags_metadata = [
    {
        "name": "health",
        "description": "Health check endpoint untuk monitoring dan Docker healthcheck.",
    },
    {
        "name": "analytics",
        "description": "Kalkulasi harga, volatilitas, risk score, dan ranking komoditas/wilayah.",
    },
    {
        "name": "alerts",
        "description": "Sistem peringatan dini — deteksi lonjakan harga abnormal.",
    },
    {
        "name": "insights",
        "description": "Ringkasan analitik otomatis (harian/mingguan).",
    },
    {
        "name": "forecast",
        "description": "Prediksi harga komoditas menggunakan model Prophet.",
    },
    {
        "name": "drivers",
        "description": "Analisis faktor penggerak perubahan harga (cuaca, energi, supply).",
    },
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the in-process validation pipeline (Redis Streams consumer). If Redis is
    # unavailable the API still serves; report validation just queues best-effort.
    pipeline = ValidationPipeline()
    try:
        await pipeline.start()
    except Exception:
        logger.warning("ValidationPipeline failed to start (Redis unavailable?)", exc_info=True)
    app.state.validation_pipeline = pipeline

    # Refresh worker consumes stream:validation_done — incrementally rebuilds
    # feature_store_daily + analytics_forecast for pairs touched by APPROVED crowd
    # reports. Debounced ~15min. Same graceful-degradation pattern.
    refresh = RefreshWorker()
    try:
        await refresh.start()
    except Exception:
        logger.warning("RefreshWorker failed to start (Redis unavailable?)", exc_info=True)
    app.state.refresh_worker = refresh

    yield

    try:
        await refresh.stop()
    except Exception:
        pass
    try:
        await pipeline.stop()
    except Exception:
        pass
    await close_redis()


app = FastAPI(
    lifespan=lifespan,
    title="INFLASI Analytics API",
    description=DESCRIPTION,
    version="0.1.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "INFLASI Team",
        "url": "https://inflasi.id",
    },
    license_info={
        "name": "MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://inflasi.id", "http://web:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# Prometheus metrics at /metrics (scraped by inflasi-monitoring).
Instrumentator().instrument(app).expose(app)


@app.get("/health", tags=["health"], summary="Health Check")
async def health_check():
    """Cek apakah service berjalan. Digunakan oleh Docker healthcheck dan load balancer."""
    return {"status": "ok", "service": "inflasi-analytics"}
