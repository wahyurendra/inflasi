"""INFLASI ML Gateway — one FastAPI service for all ML workloads (forecast, anomaly,
OCR, trust, surplus-deficit) on a single A100. Heavy models load lazily; the service
runs CPU-only (degraded) when no GPU / no heavy libs are present.

Stateless: callers (api-gateway validation pipeline, analytics CronJob) pass the data
series in the request — the ML gateway holds no DB connection.
"""

import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import anomaly_routes, forecast_routes, ocr_routes, sd_routes, trust_routes
from app.core.device import get_device_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml-gateway")

app = FastAPI(title="INFLASI ML Gateway", version="1.0.0")

app.include_router(forecast_routes.router, prefix="/forecast", tags=["forecast"])
app.include_router(anomaly_routes.router, prefix="/anomaly", tags=["anomaly"])
app.include_router(ocr_routes.router, prefix="/ocr", tags=["ocr"])
app.include_router(trust_routes.router, prefix="/trust", tags=["trust"])
app.include_router(sd_routes.router, prefix="/surplus-deficit", tags=["surplus-deficit"])

# Prometheus metrics at /metrics (scraped by inflasi-monitoring).
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "inflasi-ml-gateway", **get_device_info()}
