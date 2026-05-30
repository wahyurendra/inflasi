import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import router as api_router
from app.core.redis import close_redis
from app.workers.forecast_batch_worker import ForecastBatchWorker
from app.workers.refresh_worker import RefreshWorker
from app.workers.retrain_worker import RetrainWorker
from app.workers.validation_pipeline import ValidationPipeline

logger = logging.getLogger("inflasi-api")

DESCRIPTION = """
Backend gateway untuk platform pemantauan inflasi pangan Indonesia.
Menyajikan data harga, prediksi multi-horizon, deteksi anomali, dan crowdsourcing
laporan harga di atas PostgreSQL + TimescaleDB, dengan ML ensemble diserve oleh
service `ml-gateway` (LightGBM / Prophet / SARIMAX / TFT / Stacking).

## Autentikasi

Endpoint publik (read-only) tidak memerlukan token. Endpoint user (reports,
notifications, gamification) dan admin (`/admin/*`) memerlukan **Firebase ID
token** di header:

```
Authorization: Bearer <FIREBASE_ID_TOKEN>
```

Klik tombol **Authorize** di kanan atas untuk inject token ke semua endpoint
saat mencoba. Role-based access (ADMIN / GOVERNMENT_ANALYST / CONTRIBUTOR /
REPORTER) di-resolve di Postgres berdasarkan `firebase_uid`.

## Forecasting v2

`POST /api/forecast/price` mengembalikan quantile forecast (p10/p50/p90),
risk level, top drivers, dan kontribusi tiap base-model. Versi model di-stamp
dari `model_registry` (lihat `/api/admin/models`). Persist ke
`analytics_forecast` + `forecast_model_components`.

## Data Sources

| Sumber | Layer | Frekuensi |
|--------|-------|-----------|
| PIHPS Bank Indonesia | `fact_price_daily` | Harian |
| BPS | `fact_inflation_monthly` | Bulanan |
| BMKG | `fact_climate` | Harian |
| BAPANAS | `fact_supply_stock` | Harian |
| FAO Food Price Index | `ext_fao_food_price` | Bulanan |
| World Bank Commodities | `ext_commodity_price` | Bulanan |
| EIA Energy | `ext_energy_price` | Harian |
| BI JISDOR / ECB | `ext_exchange_rate`, `fact_macro_driver` | Harian |
| GSCPI | `ext_supply_chain_index` | Bulanan |

## Konvensi

- Semua tanggal: ISO 8601 (`YYYY-MM-DD`).
- Mata uang: IDR.
- Error: `{"detail": "<message>"}` dengan status code HTTP standar
  (400 invalid body, 401 unauth, 403 forbidden, 404 not found, 422 validation,
  500 internal).
- Pagination: `?limit=&offset=` di endpoint list.
"""

tags_metadata = [
    # ── Meta ──────────────────────────────────────────────────
    {"name": "health", "description": "Health check & liveness/readiness probes."},

    # ── Reference data ────────────────────────────────────────
    {"name": "regions", "description": "Master wilayah (34 provinsi + agregat nasional). Slug `kode_wilayah` digunakan sebagai foreign-key string di `feature_store_daily`."},
    {"name": "commodities", "description": "Master komoditas (beras, bawang, cabai, daging, telur, gula, tepung). Includes kategori & satuan."},
    {"name": "markets", "description": "Master pasar (`dim_market`) — normalisasi nama pasar dari laporan crowdsourcing per wilayah."},

    # ── Data layer ───────────────────────────────────────────
    {"name": "prices", "description": "Akses `fact_price_daily` — harga harian resmi/agregat. Filter per commodity/region/date range."},
    {"name": "inflation", "description": "Akses `fact_inflation_monthly` — IHK & inflasi mtm/ytd/yoy per wilayah dan kelompok."},
    {"name": "global-signals", "description": "Sinyal global: FAO Food Price Index, harga energi (EIA), kurs, GSCPI, harga komoditas dunia."},

    # ── Analytics / ML ────────────────────────────────────────
    {"name": "analytics", "description": "Agregasi & ringkasan harga: perubahan harian/mingguan/bulanan, volatilitas, ranking komoditas-wilayah."},
    {"name": "forecast", "description": "Prediksi harga multi-horizon. `POST /forecast/price` (v2) → quantile p10/p50/p90 + risk level + driver + per-model components. Legacy `GET /forecast/prices` masih tersedia."},
    {"name": "drivers", "description": "Analisis faktor penggerak perubahan harga (cuaca anomali, kurs, BBM, supply stock)."},
    {"name": "alerts", "description": "Peringatan dini — lonjakan harga, deviasi antar-wilayah, supply shortage."},
    {"name": "insights", "description": "Narasi insight auto-generated untuk dashboard (highlight harian/mingguan)."},
    {"name": "intelligence", "description": "Endpoint composite untuk dashboard intel — gabungan forecast + risk + driver dalam satu payload."},
    {"name": "recommendations", "description": "Rekomendasi aksi (intervensi pasar / pengadaan) berdasarkan risk score dan supply chain index."},
    {"name": "ai", "description": "AI context endpoints — narasi & ringkasan natural-language siap untuk LLM downstream."},

    # ── User-facing (auth required) ──────────────────────────
    {"name": "auth", "description": "Sign-in flow via Firebase. Tukar Firebase ID token dengan session user di Postgres."},
    {"name": "users", "description": "Profil user, role management. Endpoint `/admin/list` & `/admin/stats` butuh role ADMIN."},
    {"name": "reports", "description": "Laporan harga crowdsourcing (`price_reports`). Workflow: submit → validation pipeline → APPROVED/FLAGGED/REJECTED."},
    {"name": "notifications", "description": "Notifikasi user (alert harga, badge, status laporan)."},
    {"name": "gamification", "description": "Sistem poin, streak, dan badge untuk kontributor."},

    # ── Admin & internal ─────────────────────────────────────
    {
        "name": "admin-models",
        "description": (
            "Model registry — list, register, promote ke active. Wajib role "
            "ADMIN atau GOVERNMENT_ANALYST. Promosi mengaktifkan satu model "
            "per slot `(model_type, target_type, horizon)`; versi yang sebelumnya "
            "active otomatis dinonaktifkan."
        ),
    },
    {
        "name": "internal",
        "description": (
            "Endpoint service-to-service (dipanggil ml-gateway / worker). Tidak "
            "ada autentikasi — diasumsikan hanya reachable via ClusterIP / "
            "internal network. Jangan expose ke ingress."
        ),
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

    # Batch forecast worker — listens for admin-triggered /batch-run requests
    # and runs the full ml-gateway forecast loop over every active pair.
    batch_worker = ForecastBatchWorker()
    try:
        await batch_worker.start()
    except Exception:
        logger.warning(
            "ForecastBatchWorker failed to start (Redis unavailable?)", exc_info=True,
        )
    app.state.forecast_batch_worker = batch_worker

    # Retrain worker — listens for admin-triggered /retrain requests and
    # spawns the trainer subprocess inside this pod. Always optional.
    retrain_worker = RetrainWorker()
    try:
        await retrain_worker.start()
    except Exception:
        logger.warning(
            "RetrainWorker failed to start (Redis unavailable?)", exc_info=True,
        )
    app.state.retrain_worker = retrain_worker

    yield

    for w in (retrain_worker, batch_worker, refresh, pipeline):
        try:
            await w.stop()
        except Exception:
            pass
    await close_redis()


app = FastAPI(
    lifespan=lifespan,
    title="INFLASI API",
    summary="Food-inflation monitoring + forecasting backend (FastAPI + TimescaleDB + ml-gateway).",
    description=DESCRIPTION,
    version="0.2.0",  # v2 quantile forecast + model_registry + dim_market
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "docExpansion": "none",       # tutup semua tag by default — daftar tag panjang
        "defaultModelsExpandDepth": 1,
        "persistAuthorization": True,  # token bertahan setelah refresh
        "tryItOutEnabled": True,
        "filter": True,                # search bar di Swagger UI
    },
    servers=[
        {"url": "/", "description": "Server saat ini (relative)"},
        {"url": "http://localhost:8000", "description": "Local dev"},
        {"url": "https://api.inflasi.id", "description": "Production"},
    ],
    contact={
        "name": "INFLASI Team",
        "url": "https://inflasi.id",
        "email": "team@inflasi.id",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
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
