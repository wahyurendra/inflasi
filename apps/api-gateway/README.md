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
│   │   ├── drivers.py        # Driver analysis
│   │   └── blog.py           # Auto-generated blog (list / detail / generate)
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
│       ├── blog_generator.py   # Daily analytics → ≥1500-word blog article (OpenAI + fallback)
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
| `OPENAI_API_KEY` | OpenAI key untuk generator blog harian (kosong → fallback template) | Tidak |
| `OPENAI_MODEL` | Model OpenAI untuk blog (default `gpt-5.4-mini`) | Tidak |
| `BLOG_GENERATION_ENABLED` | Aktifkan generasi blog di batch analitik (default `true`) | Tidak |

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
| GET | `/api/blog` | Daftar artikel blog terbit |
| GET | `/api/blog/{slug}` | Detail artikel blog |
| POST | `/api/blog/generate` | Generate artikel manual (default hari ini) |

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
| 17:30 | Analytics | Risk scores, Alerts, Anomalies, Insights, **Blog harian** |

## Blog Otomatis

Setiap batch analitik harian (`run_analytics.py`, dijalankan oleh CronJob `inflasi-analytics`)
menghasilkan satu artikel blog publik dari data hari itu — di-hook setelah langkah insight dan
diisolasi dengan `try/except` agar kegagalan tidak menggagalkan batch.

- **Sumber narasi:** `BlogGenerator` (`app/services/blog_generator.py`) mengumpulkan headline
  inflasi, komoditas naik/turun, provinsi tertekan, alert aktif, driver komoditas teratas, serta
  konteks makro (kurs, FAO, GSCPI) dan volatilitas (CV 30 hari).
- **Penulisan:** OpenAI (`OPENAI_MODEL`, default `gpt-5.4-mini`) menulis artikel Markdown
  **minimal 1500 kata** dengan aturan anti-halusinasi (hanya angka dari data). Jika `OPENAI_API_KEY`
  kosong atau panggilan gagal, jatuh ke **template deterministik** yang tetap komprehensif.
- **Referensi:** tiap artikel diakhiri bagian `## Referensi` berisi sumber resmi (PIHPS BI, BPS,
  BMKG, JISDOR, FAO, Fed NY GSCPI, Bapanas) yang dipilih dari sinyal yang benar-benar dipakai.
- **Penyimpanan:** tabel `content_blog_posts` (migrasi `0010`), satu baris per `(tanggal, tipe)`
  via upsert idempoten. Status `published` langsung tampil di `/api/blog`.

```bash
# Generate manual untuk tanggal tertentu (atau default hari ini)
python run_analytics.py 2026-05-29          # bagian dari batch lengkap
curl -X POST 'http://localhost:8001/api/blog/generate?tanggal=2026-05-29'
```

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
