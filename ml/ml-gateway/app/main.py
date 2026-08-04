"""INFLASI ML Gateway — one API deployed as an always-on CPU frontend and a
preemptible GPU backend. Heavy models load lazily; TFT/OCR degrade cleanly while
the single GPU is occupied by training.

Stateless: callers (api-gateway validation pipeline, analytics CronJob) pass the data
series in the request — the ML gateway holds no DB connection.
"""

import logging
import os

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import (
    anomaly_routes, forecast_routes, gpu_routes, inflation_routes,
    ocr_routes, sd_routes, trust_routes,
)
from app.core.device import get_device_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml-gateway")

app = FastAPI(title="INFLASI ML Gateway", version="1.0.0")

app.include_router(forecast_routes.router, prefix="/forecast", tags=["forecast"])
app.include_router(inflation_routes.router, prefix="/inflation", tags=["forecast"])
app.include_router(anomaly_routes.router, prefix="/anomaly", tags=["anomaly"])
app.include_router(ocr_routes.router, prefix="/ocr", tags=["ocr"])
app.include_router(trust_routes.router, prefix="/trust", tags=["trust"])
app.include_router(sd_routes.router, prefix="/surplus-deficit", tags=["surplus-deficit"])
app.include_router(gpu_routes.router, prefix="/internal/gpu", tags=["internal-gpu"])

# Prometheus metrics at /metrics (scraped by inflasi-monitoring).
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "inflasi-ml-gateway",
        "role": os.environ.get("WORKLOAD_ROLE", "standalone"),
        **get_device_info(),
    }


@app.get("/ready")
async def ready() -> dict:
    """GPU pods are ready only when CUDA is actually visible."""
    info = get_device_info()
    require_gpu = os.environ.get("REQUIRE_GPU", "false").lower() in {"1", "true", "yes"}
    if require_gpu and not info.get("gpu"):
        raise HTTPException(status_code=503, detail="CUDA GPU is required but unavailable")
    return {"status": "ready", **info}
