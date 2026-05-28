# INFLASI ML Gateway

One FastAPI service for all ML workloads, on a single A100 (CPU-fallback when no GPU).
**Stateless** — callers pass the data series in the request; no DB connection.

## Endpoints
| Route | Purpose | Compute |
|---|---|---|
| `POST /forecast/prices` | Ensemble forecast (ARIMA + Prophet + TFT) | CPU + GPU (TFT) |
| `POST /anomaly/detect` | Price anomaly (z-score baseline) | CPU |
| `POST /ocr/verify` | Receipt/label price verification (PaddleOCR) | GPU |
| `POST /trust/score` | Contributor trust score | CPU |
| `POST /surplus-deficit/classify` | Regional surplus/deficit | CPU |
| `GET /health` | Status + GPU/VRAM info | — |

## Graceful degradation
Heavy libs (torch, pytorch-forecasting, paddleocr) are imported lazily. Without them /
without a GPU: TFT drops out of the ensemble and OCR returns `available: false`; the
CPU models (ARIMA/Prophet/anomaly/trust/SD) keep working.

## Run
- GPU: build `Dockerfile.gpu`, deploy via `infra/k8s/projects/inflasi-ml` (Recreate,
  `runtimeClassName: nvidia`, `nvidia.com/gpu: 1`). Needs the NVIDIA device plugin on the node.
- Local CPU: `pip install -r requirements.txt && uvicorn app.main:app --port 8080`.

Callers reach it in-cluster at `http://inflasi-ml:8080`.
