# CPU training image — runs export_dataset, train_lightgbm, train_prophet,
# train_sarimax, train_ensemble. TFT training needs torch and lives in the
# GPU image (Dockerfile.gpu, mirrors ml-gateway's GPU build).
#
# The image mounts the repo at /workspace so it can import
# app.services.feature_encoder via ml/training/encoder.py without packaging.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/workspace

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY ml/training/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copy both the trainers and the shared feature encoder.
COPY ml/training/ /workspace/ml/training/
COPY apps/api-gateway/app/services/feature_encoder.py /workspace/apps/api-gateway/app/services/feature_encoder.py

# Default entrypoint runs python; each K8s Job passes a script as an arg.
ENTRYPOINT ["python", "-m"]
CMD ["ml.training.export_dataset"]
