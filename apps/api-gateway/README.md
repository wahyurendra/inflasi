# Inflasi API

Backend analytics engine untuk platform pemantauan inflasi pangan Indonesia.

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL (Supabase) via SQLAlchemy async + asyncpg
- **ETL**: Custom pipeline framework dengan 7 sumber data
- **Scheduler**: APScheduler (cron-based, timezone Asia/Jakarta)
- **Forecasting**: Prophet, scikit-learn
- **HTTP Client**: httpx

## Arsitektur

```
inflasi-api/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Pydantic settings
│   ├── database.py           # SQLAlchemy async session
│   ├── api/endpoints/        # REST API endpoints
│   │   ├── analytics.py      # Harga, volatilitas, risk scores
│   │   ├── alerts.py         # Alert management
│   │   ├── insights.py       # Insight generation
│   │   ├── forecast.py       # Price forecasting
│   │   └── drivers.py        # Driver analysis
│   ├── etl/pipelines/        # ETL pipelines
│   │   ├── pihps_bi.py       # Harga pangan harian (Bank Indonesia)
│   │   ├── exchange_rate.py  # Kurs USD/IDR (ECB)
│   │   ├── energy_price.py   # Harga energi (EIA / World Bank)
│   │   ├── fao_food_price.py # FAO Food Price Index
│   │   ├── commodity_global.py # Komoditas global (World Bank)
│   │   ├── gdelt_news.py     # News intelligence (GDELT)
│   │   └── bmkg_weather.py   # Data cuaca (BMKG)
│   └── services/             # Business logic
│       ├── risk_scorer.py
│       ├── alert_engine.py
│       ├── anomaly_detector.py
│       ├── forecast_engine.py
│       ├── insight_generator.py
│       ├── price_calculator.py
│       ├── ranking.py
│       ├── driver_analyzer.py
│       └── supply_demand.py
├── run_etl.py                # CLI runner untuk ETL
├── scheduler.py              # APScheduler cron jobs
├── Dockerfile.api            # Docker image untuk API
├── Dockerfile.etl            # Docker image untuk ETL/scheduler
└── docker-compose.yml        # Orchestration
```

## Setup

### Environment Variables

Copy `.env.example` dan isi dengan credential yang sesuai:

```bash
cp .env.example .env
```

| Variable | Deskripsi | Required |
|----------|-----------|----------|
| `ANALYTICS_DATABASE_URL` | PostgreSQL connection string (asyncpg) | Ya |
| `DATABASE_URL` | Fallback database URL | Ya |
| `EIA_API_KEY` | US Energy Information Administration API key | Tidak (ada fallback) |
| `BPS_API_KEY` | Badan Pusat Statistik API key | Tidak |
| `ANTHROPIC_API_KEY` | Claude AI API key | Tidak |

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan API
uvicorn app.main:app --reload --port 8000

# Jalankan scheduler
python scheduler.py

# Jalankan ETL manual
python run_etl.py --pipeline pihps --days 7 --verbose
```

### Docker

```bash
# Build dan start semua service
docker compose up -d

# Build ulang setelah ada perubahan kode
docker compose up -d --build

# Lihat logs
docker compose logs -f api
docker compose logs -f etl

# Run ETL manual (one-off)
docker compose run --rm etl python run_etl.py --pipeline pihps --verbose

# Stop semua service
docker compose down
```

**Services:**

| Service | Dockerfile | Port | Deskripsi |
|---------|------------|------|-----------|
| `api` | `Dockerfile.api` | 8000 | FastAPI REST API |
| `etl` | `Dockerfile.etl` | - | Scheduler + ETL worker (background) |

## API Endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/api/analytics/prices/changes` | Perubahan harga |
| GET | `/api/analytics/prices/volatility` | Volatilitas harga |
| GET | `/api/analytics/risk-scores` | Risk scores per komoditas |
| GET | `/api/analytics/commodities/ranking` | Ranking komoditas |
| GET | `/api/analytics/regions/ranking` | Ranking wilayah |
| GET | `/api/alerts/active` | Alert aktif |
| POST | `/api/alerts/generate` | Generate alert harian |
| GET | `/api/forecast/...` | Prediksi harga |
| GET | `/api/insights/...` | Insight harian |
| GET | `/api/drivers/...` | Analisis driver |

## ETL Pipelines

```bash
python run_etl.py [OPTIONS]
```

| Option | Default | Deskripsi |
|--------|---------|-----------|
| `--pipeline`, `-p` | `all` | Pipeline: `pihps`, `kurs`, `energy`, `fao`, `commodity`, `news`, `bmkg`, `global`, `all` |
| `--days` | `7` | Jumlah hari ke belakang |
| `--date` | - | Tanggal spesifik (YYYY-MM-DD) |
| `--verbose`, `-v` | - | Log detail |

## Scheduler

Jadwal otomatis (WIB):

| Waktu | Job | Pipelines |
|-------|-----|-----------|
| 06:00 | Global datasets | Kurs, Energy, FAO, Commodity, News |
| 10:30 | PIHPS BI (pagi) | Harga pangan harian |
| 13:30 | PIHPS BI (siang) | Harga pangan harian |
| 14:00 | BMKG Weather | Data cuaca |
| 17:30 | Analytics | Risk scores, Alerts, Anomalies, Insights |

## Sumber Data

| Sumber | Data | API Key |
|--------|------|---------|
| Bank Indonesia (PIHPS) | Harga pangan harian | Tidak |
| ECB / Frankfurter | Kurs USD/IDR | Tidak |
| US EIA | Harga energi (Brent crude) | Ya (gratis) |
| World Bank | Komoditas global | Tidak |
| FAO | Food Price Index | Tidak |
| GDELT | News intelligence | Tidak |
| BMKG | Prakiraan cuaca | Tidak |
