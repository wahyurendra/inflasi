FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2, lxml, prophet (cmdstan)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (separate layer for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app package + Alembic migrations (init-container runs `alembic upgrade head`)
COPY app/ ./app/
COPY alembic.ini ./alembic.ini
COPY alembic/ ./alembic/

# ETL / analytics entrypoints — invoked by k8s CronJobs via `command:` override
# on this same image (no separate ETL image needed).
COPY run_etl.py run_analytics.py ./

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=40s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
