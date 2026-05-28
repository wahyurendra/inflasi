# CPU image for the ML gateway. Used by CI (push to GHCR) and CPU-only deploys.
# Forecast (ARIMA + Prophet), anomaly, trust, surplus-deficit all work here.
# TFT and OCR routes degrade gracefully (return "unavailable") without GPU libs.
# For the full GPU image (A100 node), see Dockerfile.gpu.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app/ ./app/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=60s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
