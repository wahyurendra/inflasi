# INFLASI — MVP Blueprint
## Sistem Pemantauan Inflasi Pangan Berbasis AI

> *"Sistem pemantauan inflasi pangan dengan AI yang membantu membaca sinyal dini, menjelaskan penyebab awal, dan memprioritaskan wilayah/komoditas yang perlu diintervensi."*

---

## 1. Ringkasan Eksekutif MVP

Platform INFLASI adalah sistem pemantauan inflasi pangan berbasis AI yang dirancang untuk membantu pengambil kebijakan, analis ekonomi, dan tim pemantauan harga dalam:

- **Membaca sinyal dini** tekanan harga pangan sebelum menjadi krisis
- **Mengidentifikasi** komoditas dan wilayah yang membutuhkan perhatian segera
- **Menyediakan insight otomatis** berbasis data, bukan opini
- **Memungkinkan tanya-jawab langsung** ke data melalui AI assistant

MVP berfokus pada **inflasi pangan** dengan 8 komoditas strategis, 6 sumber data resmi, dan cakupan wilayah nasional + provinsi. Target penyelesaian: **8–10 minggu**.

**Apa yang membedakan dari dashboard inflasi biasa:**
- Bukan hanya menampilkan angka, tapi **menjelaskan mengapa** angka berubah
- Bukan hanya grafik historis, tapi **alert dini** berbasis rule
- Bukan hanya visualisasi, tapi **AI assistant** yang bisa menjawab pertanyaan kontekstual

---

## 2. Tujuan Bisnis dan Nilai Produk

### Tujuan Bisnis
| # | Tujuan | Metrik Sukses |
|---|--------|---------------|
| 1 | Mempercepat deteksi tekanan harga pangan | Alert muncul ≤24 jam setelah anomali terjadi |
| 2 | Mengurangi waktu analisis manual | Waktu insight dari >2 jam menjadi <5 menit |
| 3 | Menyediakan single source of truth inflasi pangan | 1 platform menggabungkan 6 sumber data |
| 4 | Membantu prioritisasi intervensi | Risk score per komoditas & wilayah tersedia |

### Value Proposition per User Persona

| Persona | Pain Point | Nilai yang Diberikan |
|---------|-----------|---------------------|
| **Pengambil Kebijakan** | Data tersebar, lambat dapat insight | Overview 1 layar + AI summary |
| **Analis Ekonomi** | Manual cross-reference banyak sumber | Data terintegrasi + perbandingan otomatis |
| **Operator Pemantauan** | Sulit deteksi anomali harga dini | Alert otomatis + risk scoring |
| **Internal User** | Perlu jawaban cepat dari data | AI chat langsung ke data |

---

## 3. Daftar Fitur Inti MVP

### Prioritas 1 — Wajib Ada di MVP
| # | Fitur | Deskripsi |
|---|-------|-----------|
| F1 | **Dashboard Headline Inflasi** | IHK nasional, mtm, ytd, yoy + tren |
| F2 | **Tren Harga Harian Komoditas** | Line chart harga 8 komoditas utama |
| F3 | **Heatmap/Ranking Wilayah** | Peta tekanan harga per provinsi |
| F4 | **Alert Anomali Harga** | Rule-based alert dengan severity |
| F5 | **AI Chat Q&A** | Tanya jawab berbasis data dashboard |
| F6 | **Insight Otomatis** | Ringkasan harian/mingguan otomatis |

### Prioritas 2 — Nice to Have di MVP
| # | Fitur | Deskripsi |
|---|-------|-----------|
| F7 | Perbandingan antarwilayah | Side-by-side comparison 2 wilayah |
| F8 | Inflation Risk Score | Skor risiko per komoditas-wilayah |
| F9 | Drill-down per wilayah | Detail komoditas per provinsi/kota |

### Prioritas 3 — Post-MVP
| # | Fitur | Deskripsi |
|---|-------|-----------|
| F10 | Forecasting harga | Prediksi harga 7–30 hari |
| F11 | Simulasi kebijakan | What-if analysis |
| F12 | Multi-role access | Role-based dashboard views |
| F13 | Export & reporting | PDF/Excel export otomatis |

### Komoditas Prioritas MVP
1. Beras
2. Cabai merah
3. Cabai rawit
4. Bawang merah
5. Bawang putih
6. Telur ayam ras
7. Minyak goreng
8. Gula pasir

### Cakupan Wilayah MVP
- **Level 1:** Nasional (agregat)
- **Level 2:** 34 Provinsi
- **Level 3:** 5–10 kota utama (Jakarta, Surabaya, Medan, Makassar, Bandung, Semarang, Yogyakarta, Denpasar, Palembang, Balikpapan) — jika data tersedia

---

## 4. Arsitektur Sistem Tingkat Tinggi

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │  Dashboard UI │  │  AI Chat UI  │  │  Alert Notif (Web) │     │
│  │  (Next.js)   │  │  (Chat Panel)│  │                    │     │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘     │
│         │                 │                    │                  │
└─────────┼─────────────────┼────────────────────┼─────────────────┘
          │                 │                    │
┌─────────┼─────────────────┼────────────────────┼─────────────────┐
│         ▼                 ▼                    ▼   API LAYER     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              API Gateway (Next.js API Routes)           │     │
│  └────┬──────────────┬──────────────────┬──────────────────┘     │
│       │              │                  │                        │
│  ┌────▼────┐  ┌──────▼───────┐  ┌──────▼──────────┐            │
│  │Analytics│  │ AI Query     │  │ Alert            │            │
│  │ API     │  │ Orchestrator │  │ Engine           │            │
│  └────┬────┘  └──────┬───────┘  └──────┬──────────┘            │
│       │              │                  │                        │
└───────┼──────────────┼──────────────────┼────────────────────────┘
        │              │                  │
┌───────┼──────────────┼──────────────────┼────────────────────────┐
│       ▼              ▼                  ▼   PROCESSING LAYER    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              Analytics Engine (Python)                │       │
│  │  ┌──────────┐ ┌───────────┐ ┌────────────────────┐  │       │
│  │  │ Trend    │ │ Risk      │ │ Insight            │  │       │
│  │  │ Calc     │ │ Scoring   │ │ Generator          │  │       │
│  │  └──────────┘ └───────────┘ └────────────────────┘  │       │
│  └──────────────────────┬───────────────────────────────┘       │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────┐       │
│  │              Semantic/Query Layer                      │       │
│  │  (Structured query builder for AI — NOT raw SQL)      │       │
│  └──────────────────────┬───────────────────────────────┘       │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          │
┌─────────────────────────┼────────────────────────────────────────┐
│                         ▼            DATA LAYER                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              PostgreSQL Database                       │       │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐  │       │
│  │  │ Staging │ │  Mart   │ │   Dims   │ │  Cache   │  │       │
│  │  │ Tables  │ │ (Facts) │ │          │ │          │  │       │
│  │  └─────────┘ └─────────┘ └──────────┘ └──────────┘  │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              ETL Pipeline (Python + Cron)             │       │
│  │  BPS → PIHPS BI → Bapanas → JISDOR → BMKG → Calendar│       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Komponen Utama

| Layer | Teknologi | Fungsi |
|-------|-----------|--------|
| **Frontend** | Next.js 14 + TypeScript | Dashboard UI, Chart, AI Chat |
| **API** | Next.js API Routes | REST endpoints untuk data & AI |
| **Analytics** | Python (FastAPI) | Kalkulasi, scoring, insight generation |
| **AI** | Claude API + Semantic Layer | Query interpretation & response |
| **Database** | PostgreSQL + Redis | Data store + caching |
| **ETL** | Python scripts + cron | Data ingestion pipeline |
| **Infra** | Vercel (FE) + Railway/Fly.io (BE) | Hosting MVP |

---

## 5. Desain Data dan Skema Tabel Inti

### 5.1 Entity Relationship Diagram (Konseptual)

```
dim_region ────────┐
                   ├──→ fact_inflation_monthly
dim_commodity ─────┤
                   ├──→ fact_price_daily
dim_region ────────┤
                   ├──→ fact_supply_stock
                   │
                   ├──→ fact_climate
                   │
                   └──→ fact_macro_driver

dim_calendar ──────────→ (semua fact tables via tanggal)
```

### 5.2 Dimension Tables

#### `dim_region`
```sql
CREATE TABLE dim_region (
    id              SERIAL PRIMARY KEY,
    kode_wilayah    VARCHAR(10) UNIQUE NOT NULL,  -- Kode BPS
    nama_provinsi   VARCHAR(100) NOT NULL,
    nama_kab_kota   VARCHAR(100),                 -- NULL untuk level provinsi
    level_wilayah   VARCHAR(20) NOT NULL,          -- 'nasional', 'provinsi', 'kab_kota'
    latitude        DECIMAL(10, 7),
    longitude       DECIMAL(10, 7),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_region_level ON dim_region(level_wilayah);
CREATE INDEX idx_region_provinsi ON dim_region(nama_provinsi);
```

#### `dim_commodity`
```sql
CREATE TABLE dim_commodity (
    id              SERIAL PRIMARY KEY,
    kode_komoditas  VARCHAR(20) UNIQUE NOT NULL,
    nama_komoditas  VARCHAR(100) NOT NULL,
    nama_display    VARCHAR(100) NOT NULL,         -- Nama tampilan di UI
    kategori        VARCHAR(50) NOT NULL,          -- 'bahan_pokok', 'bumbu', 'protein', 'minyak_gula'
    satuan          VARCHAR(20) NOT NULL,          -- 'kg', 'liter', 'butir'
    is_strategis    BOOLEAN DEFAULT FALSE,
    is_mvp          BOOLEAN DEFAULT TRUE,          -- Komoditas yang masuk MVP
    created_at      TIMESTAMP DEFAULT NOW()
);
```

#### `dim_calendar`
```sql
CREATE TABLE dim_calendar (
    tanggal         DATE PRIMARY KEY,
    tahun           INTEGER NOT NULL,
    bulan           INTEGER NOT NULL,
    minggu_ke       INTEGER NOT NULL,
    hari_ke         INTEGER NOT NULL,
    nama_hari       VARCHAR(20) NOT NULL,
    is_weekend      BOOLEAN DEFAULT FALSE,
    is_hari_libur   BOOLEAN DEFAULT FALSE,
    nama_libur      VARCHAR(100),
    musim           VARCHAR(50),                   -- 'ramadan', 'idulfitri', 'nataru', 'panen_raya', 'paceklik', 'normal'
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Pre-populate: 2023-01-01 sampai 2027-12-31
```

### 5.3 Fact Tables

#### `fact_inflation_monthly`
```sql
CREATE TABLE fact_inflation_monthly (
    id              SERIAL PRIMARY KEY,
    periode         DATE NOT NULL,                 -- Selalu tanggal 1 bulan tersebut
    region_id       INTEGER REFERENCES dim_region(id),
    level_wilayah   VARCHAR(20) NOT NULL,
    ihk             DECIMAL(10, 2),
    inflasi_mtm     DECIMAL(8, 4),                 -- Month-to-month (%)
    inflasi_ytd     DECIMAL(8, 4),                 -- Year-to-date (%)
    inflasi_yoy     DECIMAL(8, 4),                 -- Year-on-year (%)
    kelompok        VARCHAR(100),                  -- Kelompok pengeluaran BPS
    commodity_id    INTEGER REFERENCES dim_commodity(id),
    andil           DECIMAL(8, 4),                 -- Andil inflasi (%)
    sumber          VARCHAR(50) DEFAULT 'BPS',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),

    UNIQUE(periode, region_id, kelompok, commodity_id)
);

CREATE INDEX idx_inflation_periode ON fact_inflation_monthly(periode);
CREATE INDEX idx_inflation_region ON fact_inflation_monthly(region_id);
CREATE INDEX idx_inflation_commodity ON fact_inflation_monthly(commodity_id);
```

#### `fact_price_daily`
```sql
CREATE TABLE fact_price_daily (
    id                  SERIAL PRIMARY KEY,
    tanggal             DATE NOT NULL,
    region_id           INTEGER REFERENCES dim_region(id),
    commodity_id        INTEGER REFERENCES dim_commodity(id),
    harga               DECIMAL(12, 2) NOT NULL,       -- Harga dalam Rupiah
    harga_kemarin       DECIMAL(12, 2),
    perubahan_harian    DECIMAL(8, 4),                 -- % change vs kemarin
    perubahan_mingguan  DECIMAL(8, 4),                 -- % change vs 7 hari lalu
    perubahan_bulanan   DECIMAL(8, 4),                 -- % change vs 30 hari lalu
    sumber              VARCHAR(50) DEFAULT 'PIHPS_BI',
    created_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE(tanggal, region_id, commodity_id)
);

CREATE INDEX idx_price_tanggal ON fact_price_daily(tanggal);
CREATE INDEX idx_price_commodity ON fact_price_daily(commodity_id);
CREATE INDEX idx_price_region ON fact_price_daily(region_id);
CREATE INDEX idx_price_tanggal_commodity ON fact_price_daily(tanggal, commodity_id);
```

#### `fact_supply_stock`
```sql
CREATE TABLE fact_supply_stock (
    id              SERIAL PRIMARY KEY,
    tanggal         DATE NOT NULL,
    region_id       INTEGER REFERENCES dim_region(id),
    commodity_id    INTEGER REFERENCES dim_commodity(id),
    stok            DECIMAL(15, 2),                -- Dalam ton
    cadangan        DECIMAL(15, 2),                -- Dalam ton
    status          VARCHAR(20),                   -- 'aman', 'waspada', 'kritis'
    sumber          VARCHAR(50) DEFAULT 'BAPANAS',
    created_at      TIMESTAMP DEFAULT NOW(),

    UNIQUE(tanggal, region_id, commodity_id)
);
```

#### `fact_macro_driver`
```sql
CREATE TABLE fact_macro_driver (
    id              SERIAL PRIMARY KEY,
    tanggal         DATE NOT NULL UNIQUE,
    kurs_usd_idr    DECIMAL(12, 2),               -- JISDOR
    kurs_change_pct DECIMAL(8, 4),                 -- % change vs kemarin
    harga_bbm       DECIMAL(10, 2),                -- Harga BBM (Pertalite)
    sumber_kurs     VARCHAR(50) DEFAULT 'BI_JISDOR',
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_macro_tanggal ON fact_macro_driver(tanggal);
```

#### `fact_climate`
```sql
CREATE TABLE fact_climate (
    id              SERIAL PRIMARY KEY,
    tanggal         DATE NOT NULL,
    region_id       INTEGER REFERENCES dim_region(id),
    curah_hujan     DECIMAL(8, 2),                 -- mm
    suhu_rata       DECIMAL(5, 2),                 -- Celsius
    anomali_cuaca   VARCHAR(100),                  -- Deskripsi anomali
    warning_level   VARCHAR(20),                   -- 'normal', 'waspada', 'siaga', 'awas'
    sumber          VARCHAR(50) DEFAULT 'BMKG',
    created_at      TIMESTAMP DEFAULT NOW(),

    UNIQUE(tanggal, region_id)
);

CREATE INDEX idx_climate_tanggal ON fact_climate(tanggal);
CREATE INDEX idx_climate_region ON fact_climate(region_id);
```

### 5.4 Tabel Analitik (Derived)

#### `analytics_risk_score`
```sql
CREATE TABLE analytics_risk_score (
    id                      SERIAL PRIMARY KEY,
    tanggal                 DATE NOT NULL,
    region_id               INTEGER REFERENCES dim_region(id),
    commodity_id            INTEGER REFERENCES dim_commodity(id),
    skor_kenaikan_7d        DECIMAL(5, 2),     -- 0-100
    skor_kenaikan_30d       DECIMAL(5, 2),     -- 0-100
    skor_volatilitas        DECIMAL(5, 2),     -- 0-100
    skor_deviasi_wilayah    DECIMAL(5, 2),     -- 0-100
    skor_cuaca              DECIMAL(5, 2),     -- 0-100
    skor_stok               DECIMAL(5, 2),     -- 0-100
    risk_score_total        DECIMAL(5, 2),     -- Weighted average 0-100
    risk_category           VARCHAR(20),        -- 'rendah', 'sedang', 'tinggi'
    created_at              TIMESTAMP DEFAULT NOW(),

    UNIQUE(tanggal, region_id, commodity_id)
);
```

#### `analytics_alerts`
```sql
CREATE TABLE analytics_alerts (
    id              SERIAL PRIMARY KEY,
    tanggal         DATE NOT NULL,
    region_id       INTEGER REFERENCES dim_region(id),
    commodity_id    INTEGER REFERENCES dim_commodity(id),
    alert_type      VARCHAR(50) NOT NULL,          -- 'price_spike', 'deviation', 'sustained_volatile', 'weather_price'
    severity        VARCHAR(20) NOT NULL,           -- 'info', 'warning', 'critical'
    judul           VARCHAR(200) NOT NULL,
    deskripsi       TEXT NOT NULL,
    nilai_aktual    DECIMAL(12, 2),
    nilai_threshold DECIMAL(12, 2),
    is_active       BOOLEAN DEFAULT TRUE,
    resolved_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_alerts_active ON analytics_alerts(is_active, tanggal);
CREATE INDEX idx_alerts_severity ON analytics_alerts(severity);
```

#### `analytics_insights`
```sql
CREATE TABLE analytics_insights (
    id              SERIAL PRIMARY KEY,
    tanggal         DATE NOT NULL,
    tipe            VARCHAR(20) NOT NULL,          -- 'harian', 'mingguan'
    judul           VARCHAR(200) NOT NULL,
    konten          TEXT NOT NULL,                  -- Markdown formatted
    data_snapshot   JSONB,                         -- Data pendukung insight
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 6. Alur Pipeline Data End-to-End

### 6.1 Diagram Pipeline

```
DATA SOURCES              INGESTION           STAGING          MART/ANALYTICS
─────────────             ─────────           ───────          ──────────────

BPS (IHK)          ──→  scraper_bps.py    ──→ stg_inflation ──→ fact_inflation_monthly
(Bulanan, web/API)

PIHPS BI           ──→  scraper_pihps.py  ──→ stg_price     ──→ fact_price_daily
(Harian, web)

Bapanas            ──→  scraper_bapanas.py──→ stg_supply    ──→ fact_supply_stock
(Periodik, web/API)

BI JISDOR          ──→  scraper_jisdor.py ──→ stg_macro     ──→ fact_macro_driver
(Harian, API)

BMKG               ──→  scraper_bmkg.py   ──→ stg_climate   ──→ fact_climate
(Harian, API)

Kalender Musiman   ──→  seed_calendar.py  ──→ dim_calendar  ──→ (pre-populated)

                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │  Transform &  │
                                            │  Enrich       │
                                            │  ─────────    │
                                            │  - Hitung %Δ  │
                                            │  - Risk Score │
                                            │  - Alert Check│
                                            │  - Insight Gen│
                                            └───────┬───────┘
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │ analytics_*   │
                                            │ tables        │
                                            └───────────────┘
```

### 6.2 Jadwal Pipeline

| Pipeline | Frekuensi | Waktu | Sumber |
|----------|-----------|-------|--------|
| `ingest_pihps` | Harian | 08:00 WIB | PIHPS BI |
| `ingest_jisdor` | Harian | 09:00 WIB | BI JISDOR |
| `ingest_bmkg` | Harian | 07:00 WIB | BMKG |
| `ingest_bapanas` | Mingguan/saat update | 10:00 WIB Senin | Bapanas |
| `ingest_bps` | Bulanan/saat rilis | Tanggal 1-5 | BPS |
| `calc_analytics` | Harian | 10:30 WIB (setelah ingest) | Internal |
| `gen_alerts` | Harian | 11:00 WIB | Internal |
| `gen_insights` | Harian + Mingguan | 11:30 WIB / Senin 12:00 | Internal |

### 6.3 ETL Design Principles

```python
# Pseudocode: Pipeline Pattern

class DataPipeline:
    """Base pattern untuk semua pipeline"""

    def extract(self) -> RawData:
        """Ambil data dari sumber, handle retry & timeout"""
        pass

    def validate(self, raw: RawData) -> bool:
        """Validasi: schema, range, completeness"""
        pass

    def transform(self, raw: RawData) -> CleanData:
        """Normalisasi wilayah, komoditas, format tanggal"""
        pass

    def load(self, clean: CleanData) -> None:
        """Upsert ke staging, lalu ke mart"""
        pass

    def run(self):
        raw = self.extract()
        if self.validate(raw):
            clean = self.transform(raw)
            self.load(clean)
            self.log_success()
        else:
            self.log_failure()
            self.alert_admin()
```

### 6.4 Mapping & Normalisasi

**Wilayah:** Gunakan kode BPS sebagai master key. Buat mapping table untuk mencocokkan nama wilayah dari berbagai sumber yang berbeda format.

```
PIHPS: "DKI Jakarta"    → kode_wilayah: "31"
BPS:   "Prov. DKI Jakarta" → kode_wilayah: "31"
BMKG:  "Jakarta"         → kode_wilayah: "31"
```

**Komoditas:** Gunakan kode komoditas internal sebagai master key.

```
PIHPS: "Beras Premium"      → kode_komoditas: "BERAS"
BPS:   "Beras"               → kode_komoditas: "BERAS"
Bapanas: "Beras Medium"     → kode_komoditas: "BERAS"
```

---

## 7. Desain Backend Analytics dan Alert Engine

### 7.1 Analytics Engine

#### Kalkulasi Inti

```python
# 1. Perubahan Harga
def calc_price_changes(commodity_id, region_id, tanggal):
    return {
        "harian": pct_change(harga_hari_ini, harga_kemarin),
        "mingguan": pct_change(harga_hari_ini, harga_7_hari_lalu),
        "bulanan": pct_change(harga_hari_ini, harga_30_hari_lalu),
    }

# 2. Volatilitas (Coefficient of Variation 14 hari)
def calc_volatility(commodity_id, region_id, window=14):
    prices = get_prices_last_n_days(commodity_id, region_id, window)
    return std(prices) / mean(prices) * 100

# 3. Deviasi Wilayah
def calc_regional_deviation(commodity_id, tanggal):
    prices_all_regions = get_all_region_prices(commodity_id, tanggal)
    median_nasional = median(prices_all_regions)
    return {
        region: (price - median_nasional) / median_nasional * 100
        for region, price in prices_all_regions
    }

# 4. Ranking Komoditas Penyumbang Tekanan
def get_top_pressure_commodities(tanggal, top_n=5):
    """Komoditas dengan kenaikan mingguan tertinggi (rata-rata nasional)"""
    return sorted_by_weekly_change(tanggal)[:top_n]

# 5. Ranking Wilayah Tertekan
def get_top_pressure_regions(tanggal, top_n=10):
    """Wilayah dengan rata-rata kenaikan harga tertinggi across komoditas"""
    return sorted_by_avg_price_increase(tanggal)[:top_n]
```

### 7.2 Alert Engine — Rule-Based

#### Rule Definitions

| Rule ID | Nama | Kondisi | Severity |
|---------|------|---------|----------|
| `R1` | Price Spike | Harga komoditas naik >10% dalam 7 hari | `critical` |
| `R2` | Price Rise | Harga komoditas naik >5% dalam 7 hari | `warning` |
| `R3` | Regional Deviation | Harga wilayah >20% di atas median nasional | `warning` |
| `R4` | Sustained Volatility | CV >15% selama 14 hari berturut-turut | `warning` |
| `R5` | Weather + Price | Warning BMKG ≥ siaga DAN harga naik >3% minggu ini | `critical` |
| `R6` | Multi-Commodity | ≥3 komoditas di 1 wilayah naik >5% bersamaan | `critical` |

```python
# Alert Engine Pseudocode
class AlertEngine:
    rules = [R1, R2, R3, R4, R5, R6]

    def run_daily(self, tanggal):
        new_alerts = []
        for rule in self.rules:
            triggered = rule.evaluate(tanggal)
            for item in triggered:
                alert = Alert(
                    tanggal=tanggal,
                    region_id=item.region_id,
                    commodity_id=item.commodity_id,
                    alert_type=rule.type,
                    severity=rule.severity,
                    judul=rule.format_title(item),
                    deskripsi=rule.format_description(item),
                    nilai_aktual=item.actual,
                    nilai_threshold=rule.threshold,
                )
                new_alerts.append(alert)

        # Deduplicate dan simpan
        self.save_alerts(new_alerts)

        # Auto-resolve alerts lama yang kondisinya sudah normal
        self.resolve_old_alerts(tanggal)
```

### 7.3 Inflation Risk Score

```python
def calculate_risk_score(commodity_id, region_id, tanggal):
    """
    Skor 0-100. Semakin tinggi = semakin berisiko.
    """
    weights = {
        "kenaikan_7d":      0.25,
        "kenaikan_30d":     0.20,
        "volatilitas":      0.20,
        "deviasi_wilayah":  0.15,
        "sinyal_cuaca":     0.10,
        "sinyal_stok":      0.10,
    }

    scores = {
        "kenaikan_7d":      normalize_0_100(pct_change_7d, 0, 20),
        "kenaikan_30d":     normalize_0_100(pct_change_30d, 0, 30),
        "volatilitas":      normalize_0_100(cv_14d, 0, 25),
        "deviasi_wilayah":  normalize_0_100(abs(deviation_pct), 0, 30),
        "sinyal_cuaca":     weather_to_score(warning_level),  # normal=0, waspada=33, siaga=66, awas=100
        "sinyal_stok":      stock_to_score(stock_status),     # aman=0, waspada=50, kritis=100
    }

    total = sum(scores[k] * weights[k] for k in weights)

    category = (
        "rendah" if total < 33 else
        "sedang" if total < 66 else
        "tinggi"
    )

    return total, category, scores
```

### 7.4 API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/api/inflation/headline` | IHK & inflasi nasional terbaru |
| `GET` | `/api/inflation/by-region?level=provinsi` | Inflasi per wilayah |
| `GET` | `/api/prices/daily?commodity=BERAS&region=31` | Harga harian |
| `GET` | `/api/prices/trends?commodity=BERAS&days=30` | Tren harga |
| `GET` | `/api/prices/comparison?regions=31,32` | Perbandingan wilayah |
| `GET` | `/api/commodities/ranking?sort=weekly_change` | Ranking komoditas |
| `GET` | `/api/regions/heatmap` | Data heatmap wilayah |
| `GET` | `/api/regions/ranking?sort=pressure` | Ranking wilayah |
| `GET` | `/api/alerts?active=true&severity=critical` | Daftar alert |
| `GET` | `/api/risk-scores?tanggal=2026-03-10` | Risk scores |
| `GET` | `/api/insights/latest?type=harian` | Insight terbaru |
| `POST` | `/api/ai/chat` | AI assistant chat |
| `GET` | `/api/macro/latest` | Kurs & makro terbaru |

---

## 8. Desain Dashboard per Halaman

### Halaman 1: Overview (Beranda)

**Pertanyaan utama:** *"Bagaimana kondisi inflasi pangan hari ini?"*

```
┌──────────────────────────────────────────────────────────────┐
│  INFLASI PANGAN INDONESIA                        [AI Chat 💬]│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ Inflasi MtM │ │ Inflasi YoY │ │ IHK Pangan  │            │
│  │   +0.42%    │ │   +5.21%    │ │   118.35    │            │
│  │   ▲ Feb'26  │ │   ▲ trend   │ │             │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────────┐      │
│  │ KOMODITAS PALING     │  │ WILAYAH PALING TERTEKAN  │      │
│  │ NAIK MINGGU INI      │  │ MINGGU INI               │      │
│  │ ──────────────────── │  │ ──────────────────────── │      │
│  │ 1. Cabai rawit +12%  │  │ 1. Papua +8.2%           │      │
│  │ 2. Bawang merah +7%  │  │ 2. Maluku +6.1%          │      │
│  │ 3. Telur ayam  +4%   │  │ 3. NTT +5.3%             │      │
│  │ 4. Gula pasir  +2%   │  │ 4. Sulawesi Utara +4.8%  │      │
│  │ 5. Beras       +1%   │  │ 5. Kalimantan Timur +4%  │      │
│  └──────────────────────┘  └──────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ INSIGHT HARI INI                                     │    │
│  │ ────────────────                                     │    │
│  │ Cabai rawit mengalami kenaikan 12% dalam 7 hari     │    │
│  │ terakhir, terutama di wilayah Jawa Barat dan Jawa   │    │
│  │ Timur. Kenaikan ini bertepatan dengan curah hujan    │    │
│  │ tinggi dan mendekati periode Ramadan.                │    │
│  │                                        [Baca Lengkap]│    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ALERT AKTIF (3)                         [Lihat Semua]│    │
│  │ 🔴 Cabai rawit: spike +12% / 7 hari (5 provinsi)    │    │
│  │ 🟡 Bawang merah: volatilitas tinggi 2 minggu        │    │
│  │ 🟡 Papua: 3 komoditas naik bersamaan                 │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Halaman 2: Harga Komoditas

**Pertanyaan utama:** *"Bagaimana tren harga komoditas X?"*

```
┌──────────────────────────────────────────────────────────────┐
│  HARGA KOMODITAS                                             │
├──────────────────────────────────────────────────────────────┤
│  Filter: [Beras ▼] [Nasional ▼] [30 Hari ▼]                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │          LINE CHART: Harga Beras 30 Hari             │    │
│  │  Rp/kg                                                │    │
│  │  15.000 ┤                              ╭──            │    │
│  │  14.500 ┤                    ╭─────────╯              │    │
│  │  14.000 ┤───────────────╭────╯                        │    │
│  │  13.500 ┤───────────────╯                             │    │
│  │         └──────────────────────────────────→ Tanggal  │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ RINGKASAN HARGA                                      │    │
│  │ Harga hari ini:  Rp 14.850/kg                        │    │
│  │ Perubahan harian: +0.3%  Mingguan: +1.2%             │    │
│  │ Bulanan: +3.8%           vs Tahun lalu: +7.2%        │    │
│  │ Harga tertinggi 30d: Rp 14.900 (8 Mar)               │    │
│  │ Harga terendah 30d: Rp 13.650 (15 Feb)               │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ TABEL PERUBAHAN SEMUA KOMODITAS                      │    │
│  │ Komoditas      │ Harga     │ Harian │ Minggu │ Bulan │    │
│  │ ──────────────┼───────────┼────────┼────────┼────── │    │
│  │ Cabai rawit   │ 85.000    │ +2.1%  │+12.0%  │+18.5% │    │
│  │ Bawang merah  │ 42.000    │ +0.5%  │ +7.0%  │+11.2% │    │
│  │ Telur ayam    │ 28.500    │ +0.8%  │ +4.0%  │ +6.1% │    │
│  │ Gula pasir    │ 17.200    │ +0.2%  │ +2.0%  │ +3.5% │    │
│  │ Beras         │ 14.850    │ +0.3%  │ +1.2%  │ +3.8% │    │
│  │ Minyak goreng │ 18.100    │ -0.1%  │ +0.5%  │ +1.2% │    │
│  │ Bawang putih  │ 38.000    │ +0.0%  │ -0.3%  │ +2.1% │    │
│  │ Cabai merah   │ 55.000    │ -0.5%  │ -1.2%  │ +5.3% │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Halaman 3: Peta / Wilayah

**Pertanyaan utama:** *"Wilayah mana yang paling tertekan?"*

```
┌──────────────────────────────────────────────────────────────┐
│  PETA TEKANAN HARGA                                          │
├──────────────────────────────────────────────────────────────┤
│  Filter: [Semua Komoditas ▼] [Minggu Ini ▼]                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                                                      │    │
│  │           CHOROPLETH MAP INDONESIA                   │    │
│  │     (Warna berdasarkan rata-rata kenaikan harga)     │    │
│  │                                                      │    │
│  │     🟢 Rendah (<2%)  🟡 Sedang (2-5%)                │    │
│  │     🟠 Tinggi (5-10%) 🔴 Sangat Tinggi (>10%)        │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ RANKING PROVINSI                                     │    │
│  │ #  │ Provinsi            │ Δ Harga │ Risk  │ Alert  │    │
│  │ ───┼─────────────────────┼─────────┼───────┼─────── │    │
│  │ 1  │ Papua               │ +8.2%   │Tinggi │ 2      │    │
│  │ 2  │ Maluku              │ +6.1%   │Tinggi │ 1      │    │
│  │ 3  │ NTT                 │ +5.3%   │Sedang │ 1      │    │
│  │ ...│                     │         │       │        │    │
│  │ 34 │ DKI Jakarta         │ +1.1%   │Rendah │ 0      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  [Klik provinsi untuk detail komoditas per wilayah]          │
└──────────────────────────────────────────────────────────────┘
```

### Halaman 4: Alert Center

**Pertanyaan utama:** *"Apa yang harus diwaspadai sekarang?"*

```
┌──────────────────────────────────────────────────────────────┐
│  ALERT CENTER                                                │
├──────────────────────────────────────────────────────────────┤
│  Filter: [Semua Severity ▼] [Aktif ▼] [7 Hari Terakhir ▼] │
│                                                              │
│  Ringkasan: 🔴 2 Critical  🟡 4 Warning  ℹ️ 3 Info          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 🔴 CRITICAL — 10 Mar 2026                            │    │
│  │ Cabai rawit: Kenaikan harga 12% dalam 7 hari         │    │
│  │ Wilayah: Jawa Barat, Jawa Timur, Jawa Tengah,        │    │
│  │          Sumatera Utara, Lampung                      │    │
│  │ Harga saat ini: Rp 85.000/kg (median nasional)       │    │
│  │ Threshold: >10% dalam 7 hari                         │    │
│  │ Konteks: Curah hujan tinggi + mendekati Ramadan       │    │
│  │                                     [Detail] [Tutup]  │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 🟡 WARNING — 9 Mar 2026                               │    │
│  │ Bawang merah: Volatilitas tinggi 2 minggu berturut   │    │
│  │ CV 14-hari: 18.3% (threshold: 15%)                   │    │
│  │ Wilayah: Nasional (terutama Brebes, Nganjuk)          │    │
│  │                                     [Detail] [Tutup]  │    │
│  └──────────────────────────────────────────────────────┘    │
│  ...                                                         │
└──────────────────────────────────────────────────────────────┘
```

### Halaman 5: AI Assistant

**Pertanyaan utama:** *"Saya ingin bertanya tentang data inflasi."*

```
┌──────────────────────────────────────────────────────────────┐
│  AI ASSISTANT                                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Suggested Questions:                                        │
│  ┌────────────────────────────────────────────┐              │
│  │ Komoditas apa yang paling naik minggu ini? │              │
│  │ Wilayah mana yang perlu diwaspadai?        │              │
│  │ Bagaimana tren harga beras 3 bulan ini?    │              │
│  │ Kenapa cabai rawit masuk risiko tinggi?     │              │
│  └────────────────────────────────────────────┘              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 👤 Bandingkan harga beras di Jawa Barat dan          │    │
│  │    Jawa Tengah bulan ini.                             │    │
│  │                                                      │    │
│  │ 🤖 Perbandingan Harga Beras — Maret 2026             │    │
│  │                                                      │    │
│  │ Berdasarkan data PIHPS BI (1-10 Maret 2026):         │    │
│  │                                                      │    │
│  │ • Jawa Barat: Rata-rata Rp 14.920/kg                 │    │
│  │   Tren: naik 2.1% dari Februari                       │    │
│  │                                                      │    │
│  │ • Jawa Tengah: Rata-rata Rp 14.350/kg                │    │
│  │   Tren: naik 1.8% dari Februari                       │    │
│  │                                                      │    │
│  │ Selisih: Jawa Barat lebih mahal Rp 570/kg (+4.0%).   │    │
│  │ Selisih ini relatif stabil dibanding bulan lalu.      │    │
│  │                                                      │    │
│  │ Sumber: PIHPS BI | Periode: 1-10 Maret 2026          │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Ketik pertanyaan...                        [Kirim →] │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. Desain AI Assistant, Alur Query, dan Guardrail

### 9.1 Arsitektur AI Assistant

```
USER INPUT
    │
    ▼
┌──────────────┐
│ Intent       │  Klasifikasi: descriptive, comparison, trend,
│ Classifier   │  alert_explain, summary, out_of_scope
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Query        │  Translate intent → structured query params
│ Planner      │  (commodity, region, date_range, metric)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Data         │  Execute query via API endpoints (NOT raw SQL)
│ Fetcher      │  Returns structured data + metadata
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Response     │  LLM generates narrative from structured data
│ Generator    │  Uses response templates + guardrails
│ (Claude API) │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Guardrail    │  Validate: has source, has period, no hallucination
│ Checker      │  Append metadata footer
└──────┬───────┘
       │
       ▼
RESPONSE TO USER
```

### 9.2 Intent Classification

| Intent | Contoh Pertanyaan | Query Pattern |
|--------|-------------------|---------------|
| `descriptive` | "Berapa harga beras hari ini?" | Single data point lookup |
| `comparison` | "Bandingkan harga cabai di Jabar dan Jateng" | Multi-region/commodity query |
| `trend` | "Tren harga telur 30 hari terakhir" | Time series query |
| `ranking` | "Komoditas apa yang paling naik?" | Sorted aggregation |
| `alert_explain` | "Kenapa cabai rawit risiko tinggi?" | Alert + risk score lookup |
| `summary` | "Ringkasan inflasi minggu ini" | Multiple aggregations |
| `out_of_scope` | "Prediksi harga emas tahun depan" | Reject with explanation |

### 9.3 Semantic Query Layer

```python
# Query Layer — menerjemahkan intent ke API calls

class QueryPlanner:
    def plan(self, intent: str, entities: dict) -> list[APICall]:
        """
        entities = {
            "commodity": "BERAS",
            "region": ["31", "32"],
            "date_range": "30d",
            "metric": "harga",
        }
        """
        if intent == "comparison":
            return [
                APICall("GET", "/api/prices/trends", {
                    "commodity": entities["commodity"],
                    "region": region,
                    "days": parse_days(entities["date_range"]),
                })
                for region in entities["region"]
            ]
        elif intent == "ranking":
            return [
                APICall("GET", "/api/commodities/ranking", {
                    "sort": "weekly_change",
                    "limit": 5,
                })
            ]
        # ... etc

class DataFetcher:
    def fetch(self, calls: list[APICall]) -> StructuredData:
        """Execute API calls, return combined structured result"""
        results = [self.execute(call) for call in calls]
        return self.combine(results)
```

### 9.4 Response Generation

```python
# Prompt template untuk Claude API

SYSTEM_PROMPT = """
Kamu adalah asisten analisis inflasi pangan Indonesia.
Tugasmu menjawab pertanyaan HANYA berdasarkan data yang diberikan.

ATURAN KETAT:
1. HANYA gunakan data yang ada di <data> tag. JANGAN mengarang angka.
2. SELALU sebutkan periode data dan sumber.
3. Jika data tidak tersedia, katakan "Data untuk [X] belum tersedia dalam sistem."
4. JANGAN membuat prediksi masa depan.
5. JANGAN mengarang penyebab tanpa indikator pendukung dari data.
6. Jawab dalam Bahasa Indonesia yang jelas dan ringkas.
7. Gunakan format angka Indonesia (titik untuk ribuan, koma untuk desimal).
8. Jika user bertanya di luar lingkup inflasi pangan, tolak dengan sopan.
"""

USER_PROMPT_TEMPLATE = """
Pertanyaan user: {user_question}

<data>
{structured_data_json}
</data>

<metadata>
Sumber: {sources}
Periode data: {data_period}
Terakhir diperbarui: {last_updated}
</metadata>

Jawab pertanyaan user berdasarkan data di atas. Sertakan angka spesifik dan periode.
"""
```

### 9.5 Guardrails

| # | Rule | Implementasi |
|---|------|-------------|
| G1 | Hanya dari data tersedia | LLM hanya menerima data dari query layer, bukan akses DB langsung |
| G2 | Wajib sebut periode | Post-processing: cek apakah response mengandung tanggal/periode |
| G3 | Wajib sebut sumber | Response footer otomatis: "Sumber: X \| Periode: Y" |
| G4 | Tidak boleh mengarang penyebab | Prompt instruction + hanya sediakan data indikator yang tersedia |
| G5 | Bisa bilang "tidak tahu" | Jika query result kosong, template response: "Data belum tersedia" |
| G6 | Scope check | Intent classifier menolak pertanyaan di luar inflasi pangan |
| G7 | No future prediction | Prompt instruction: tolak pertanyaan prediktif |

### 9.6 Suggested Questions Engine

```python
def generate_suggested_questions(context: DashboardContext) -> list[str]:
    """Generate pertanyaan kontekstual berdasarkan data terkini"""
    questions = []

    # Berdasarkan komoditas paling naik
    top_commodity = context.top_rising_commodity
    questions.append(
        f"Kenapa {top_commodity.nama} naik {top_commodity.pct}% minggu ini?"
    )

    # Berdasarkan alert aktif
    if context.active_alerts:
        alert = context.active_alerts[0]
        questions.append(
            f"Jelaskan alert {alert.commodity} di {alert.region}"
        )

    # Berdasarkan wilayah tertekan
    top_region = context.top_pressure_region
    questions.append(
        f"Apa yang terjadi di {top_region.nama}?"
    )

    # Default
    questions.append("Ringkasan inflasi pangan minggu ini")

    return questions[:4]
```

---

## 10. Timeline Implementasi 8–10 Minggu

```
Minggu  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │ 10
────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼────
FASE 1      │     │     │     │     │     │     │     │     │
Discovery   │     │     │     │     │     │     │     │     │
& Req.      │     │     │     │     │     │     │     │     │
────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
            │FASE 2     │     │     │     │     │     │     │
            │Data Acq.  │     │     │     │     │     │     │
            │& Pipeline │     │     │     │     │     │     │
────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
            │     │     │FASE 3     │     │     │     │     │
            │     │     │Backend    │     │     │     │     │
            │     │     │Analytics  │     │     │     │     │
────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
            │     │     │     │     │FASE 4     │     │     │
            │     │     │     │     │Dashboard  │     │     │
            │     │     │     │     │UI/UX      │     │     │
────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
            │     │     │     │     │     │     │FASE 5     │
            │     │     │     │     │     │     │AI Asst.   │
────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
            │     │     │     │     │     │     │     │     │FASE6
            │     │     │     │     │     │     │     │     │Test
────────────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴────

Parallelism notes:
- Fase 2 & 3 bisa overlap: pipeline data bisa mulai sementara analytics dikembangkan
- Fase 4 bisa mulai wireframe di minggu 4 sambil tunggu API
- Fase 5 bisa mulai prompt engineering di minggu 6
```

### Milestone per Minggu

| Minggu | Deliverable Kunci | Gate Check |
|--------|-------------------|------------|
| 1 | Requirement doc, KPI, scope locked | Stakeholder sign-off |
| 2 | Schema DB created, 2 pipeline berjalan | Data masuk ke staging |
| 3 | Semua 6 pipeline berjalan, data mart ready | Data quality >90% |
| 4 | Analytics API, alert engine MVP | Alert rule bekerja |
| 5 | Risk score, insight generation | End-to-end analytics |
| 6 | Dashboard Overview + Komoditas page | UI connected to API |
| 7 | Dashboard Peta + Alert Center | Full dashboard |
| 8 | AI chat basic, prompt tuning | AI menjawab 5 use case |
| 9 | AI refinement, integration testing | E2E test pass |
| 10 | Bug fix, hardening, demo preparation | Demo-ready |

---

## 11. Komposisi Tim dan Pembagian Peran

### Tim Ideal (6 orang)

| Peran | Tanggung Jawab | Fase Utama |
|-------|---------------|------------|
| **Product Lead / PM** | Requirement, prioritas, stakeholder management, QA | 1, 6 |
| **Data Engineer** | Pipeline ETL, schema DB, data quality | 2, 3 |
| **Backend Engineer** | API, analytics engine, alert engine | 3, 5 |
| **Frontend Engineer** | Dashboard UI, chart, responsive design | 4 |
| **Data Analyst / Economist** | Validasi data, rule definition, insight template | 1, 2, 3, 6 |
| **AI Engineer** | AI assistant, prompt engineering, guardrails | 5, 6 |

### Tim Minimal (4 orang)

| Peran | Merangkap | Fokus |
|-------|-----------|-------|
| **Lead** | PM + QA + Analyst | Strategi, validasi, testing |
| **Fullstack Engineer** | Frontend + Backend API | Next.js full-stack |
| **Data Engineer** | Pipeline + Analytics Engine | Python, DB, ETL |
| **Domain Expert + AI** | Analyst + AI prompt | Rule definition, AI tuning |

### RACI Matrix (Fase Utama)

| Aktivitas | PM | Data Eng | Backend | Frontend | Analyst | AI Eng |
|-----------|:--:|:--------:|:-------:|:--------:|:-------:|:------:|
| Requirement | A | C | C | C | R | C |
| Data Pipeline | I | A/R | C | - | C | - |
| Schema Design | C | A/R | C | - | C | - |
| Analytics Logic | C | C | A/R | - | R | - |
| Alert Rules | R | - | A | - | R | - |
| Dashboard UI | C | - | C | A/R | C | - |
| AI Assistant | C | - | C | - | C | A/R |
| Testing | A | R | R | R | R | R |

*A = Accountable, R = Responsible, C = Consulted, I = Informed*

---

## 12. KPI Keberhasilan MVP

### KPI Produk

| # | KPI | Target | Cara Ukur |
|---|-----|--------|-----------|
| 1 | Dashboard refresh sesuai jadwal | >95% uptime | Monitoring pipeline |
| 2 | Data utama masuk tanpa error | >90% completeness | Data validation log |
| 3 | AI menjawab pertanyaan inti dengan benar | >80% accuracy | Manual review 50 pertanyaan |
| 4 | Waktu insight vs manual | <5 menit vs >2 jam | User timing test |
| 5 | User bisa identifikasi prioritas | >90% user berhasil | User test scenario |

### KPI Teknis

| # | KPI | Target | Cara Ukur |
|---|-----|--------|-----------|
| 1 | Akurasi data tampilan vs sumber | 100% match | Cross-check sampling |
| 2 | Dashboard page load time | <3 detik | Lighthouse / real monitoring |
| 3 | AI response latency | <8 detik | API response time |
| 4 | Alert precision | >70% true positive | Manual validation |
| 5 | Pipeline success rate | >95% | Job monitoring |

### KPI User (Pilot)

| # | KPI | Target | Cara Ukur |
|---|-----|--------|-----------|
| 1 | Task completion rate | >85% | User test |
| 2 | Perceived usefulness (1-5) | >4.0 | Survey |
| 3 | Would recommend (NPS) | >40 | Survey |
| 4 | Pertanyaan terjawab oleh AI | >70% | Chat log analysis |

---

## 13. Risiko dan Strategi Mitigasi

| # | Risiko | Dampak | Probabilitas | Mitigasi |
|---|--------|--------|-------------|----------|
| 1 | **Data tidak konsisten** antar sumber | Tinggi | Tinggi | Master reference wilayah & komoditas; mapping table dari awal; validasi otomatis |
| 2 | **Sumber data berubah format / down** | Tinggi | Sedang | Fallback mechanism; cache data terakhir; monitoring uptime sumber |
| 3 | **Scope creep** | Sedang | Tinggi | Scope lock di Minggu 1; backlog parking lot; PM sebagai gatekeeper |
| 4 | **AI hallucination** | Tinggi | Sedang | Semantic layer (bukan raw DB); guardrails ketat; selalu tampilkan sumber & periode |
| 5 | **Dashboard terlalu kompleks** | Sedang | Sedang | 1 layar = 1 pertanyaan; user test early; progressive disclosure |
| 6 | **Pipeline rapuh** | Tinggi | Sedang | Monitoring + alerting ETL; retry logic; data validation check |
| 7 | **Tim terlalu kecil** | Sedang | Sedang | Prioritas ruthless; gunakan managed services; hindari custom infra |
| 8 | **Data BPS/PIHPS sulit di-scrape** | Sedang | Sedang | Riset awal di Fase 2; plan B: manual upload CSV jika scraping gagal |
| 9 | **Performa lambat** | Sedang | Rendah | Pre-compute analytics; Redis cache; pagination |
| 10 | **Stakeholder expectation mismatch** | Tinggi | Sedang | Demo berkala (tiap 2 minggu); alignment meeting Minggu 1 |

---

## 14. Rekomendasi Prioritas Build

### Wajib Dulu (Must Have)

```
MINGGU 1-5: Foundation
├── ✅ Pipeline data PIHPS BI (harga harian) — data inti paling bernilai
├── ✅ Pipeline data BPS (inflasi bulanan) — baseline resmi
├── ✅ Schema database + dim tables
├── ✅ API harga harian + inflasi
├── ✅ Kalkulasi perubahan harian/mingguan/bulanan
├── ✅ Alert rule sederhana (R1: price spike, R2: price rise)
└── ✅ Dashboard Overview + Komoditas page

MINGGU 6-8: Core Value
├── ✅ Dashboard Peta/Wilayah
├── ✅ Dashboard Alert Center
├── ✅ AI Chat — 3 intent utama (descriptive, trend, ranking)
└── ✅ Insight otomatis harian
```

### Bisa Ditunda ke Sprint Berikutnya

```
NICE TO HAVE — Post-MVP Sprint 1:
├── ⏳ Pipeline BMKG (cuaca)
├── ⏳ Pipeline Bapanas (stok)
├── ⏳ Pipeline JISDOR (kurs)
├── ⏳ Risk Score lengkap (perlu semua data driver)
├── ⏳ Alert rule R4, R5, R6 (butuh data cuaca & stok)
├── ⏳ Perbandingan antarwilayah di AI
├── ⏳ Insight otomatis mingguan
└── ⏳ Drill-down kota

LATER — Post-MVP Sprint 2+:
├── 🔮 Forecasting
├── 🔮 Export PDF/Excel
├── 🔮 Multi-role access
├── 🔮 Mobile responsive optimization
├── 🔮 Simulasi kebijakan
└── 🔮 Integrasi sumber data tambahan
```

**Rationale:** Fokus pertama pada PIHPS + BPS karena ini data paling stabil dan paling bernilai. Data cuaca, stok, kurs adalah *enrichment* yang memperkaya insight tapi bukan blocker untuk MVP inti.

---

## 15. Saran Tech Stack yang Realistis untuk MVP

### Frontend
| Komponen | Teknologi | Alasan |
|----------|-----------|--------|
| Framework | **Next.js 14** (App Router, TypeScript) | Full-stack, SSR, API routes built-in |
| UI Library | **shadcn/ui** + Tailwind CSS | Cepat, konsisten, accessible |
| Charts | **Recharts** atau **Tremor** | React-native, responsive, API sederhana |
| Map | **react-simple-maps** atau **Leaflet** | Choropleth Indonesia, lightweight |
| State | **TanStack Query** (React Query) | Caching, refetch, loading states |
| AI Chat UI | **Custom** (simple) atau **AI SDK** (Vercel) | Stream response, typing indicator |

### Backend
| Komponen | Teknologi | Alasan |
|----------|-----------|--------|
| API | **Next.js API Routes** + **tRPC** (opsional) | Collocated dengan frontend, type-safe |
| Analytics Engine | **Python (FastAPI)** — microservice terpisah | Pandas/NumPy untuk kalkulasi, familiar untuk data engineer |
| AI Orchestration | **Claude API** (Anthropic) + custom query layer | Kualitas bahasa Indonesia baik, tool use |
| Task Queue | **BullMQ** atau **Python Celery** | ETL scheduling, background jobs |

### Data
| Komponen | Teknologi | Alasan |
|----------|-----------|--------|
| Database | **PostgreSQL** (Supabase atau Neon) | Relational, JSON support, managed |
| Cache | **Redis** (Upstash) | API response caching, rate limiting |
| ETL | **Python scripts** + **cron** (atau GitHub Actions) | Simple, debuggable, versionable |
| File Storage | **S3-compatible** (untuk raw data backup) | Archival, cheap |

### Infrastructure
| Komponen | Teknologi | Alasan |
|----------|-----------|--------|
| Frontend Hosting | **Vercel** | Zero-config Next.js, preview deploys |
| Analytics API | **Railway** atau **Fly.io** | Simple Python deployment, auto-scale |
| Database | **Supabase** (PostgreSQL + built-in auth) | Managed, free tier generous |
| Monitoring | **Better Stack** atau **Sentry** | Error tracking, uptime monitoring |
| CI/CD | **GitHub Actions** | Standard, free for small teams |

### Diagram Tech Stack

```
┌─────────────────────────────────────────────────┐
│                   Vercel                         │
│  ┌───────────────────────────────────────────┐  │
│  │         Next.js 14 (TypeScript)           │  │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────┐  │  │
│  │  │shadcn/ui│  │ Recharts │  │ Leaflet │  │  │
│  │  └─────────┘  └──────────┘  └─────────┘  │  │
│  │  ┌──────────────────────────────────────┐ │  │
│  │  │      Next.js API Routes              │ │  │
│  │  └──────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────┘  │
└─────────────┬───────────────────┬───────────────┘
              │                   │
    ┌─────────▼─────────┐  ┌─────▼──────────┐
    │  Supabase         │  │  Railway        │
    │  (PostgreSQL)     │  │  (FastAPI)      │
    │  + Redis (Upstash)│  │  Analytics Eng. │
    └───────────────────┘  └────────┬────────┘
                                    │
                              ┌─────▼──────┐
                              │ Claude API │
                              │ (Anthropic)│
                              └────────────┘
```

### Estimasi Biaya Bulanan MVP (Managed Services)

| Service | Plan | Estimasi/bulan |
|---------|------|---------------|
| Vercel | Pro | $20 |
| Supabase | Pro | $25 |
| Railway | Starter | $5-20 |
| Upstash Redis | Free-Pay as you go | $0-10 |
| Claude API | Pay per use | $50-150 (tergantung traffic) |
| Domain | Annual | ~$1/bulan |
| **Total** | | **~$100-225/bulan** |

---

## 16. Contoh User Journey

### Skenario: Kepala Biro Kebijakan Pangan membuka dashboard pagi hari

```
09:00 — Buka Dashboard
│
├─ 1. LIHAT OVERVIEW
│     User melihat halaman Overview.
│     "Inflasi MtM Februari: +0.42%, didorong cabai rawit (+12% mingguan)"
│     Mata langsung tertuju ke box merah: "3 Alert Aktif"
│
├─ 2. CEK ALERT
│     Klik "Lihat Semua" → masuk Alert Center.
│     Lihat alert critical: "Cabai rawit spike +12% di 5 provinsi."
│     Klik Detail → lihat provinsi mana saja, grafik kenaikan.
│
├─ 3. DRILL-DOWN KOMODITAS
│     Dari alert, klik "Cabai Rawit" → masuk Harga Komoditas.
│     Lihat line chart 30 hari — tren naik tajam sejak 1 Maret.
│     Switch filter wilayah: Jawa Barat vs Nasional.
│     "Jawa Barat 15% di atas median nasional."
│
├─ 4. CEK PETA WILAYAH
│     Pindah ke Peta/Wilayah.
│     Lihat heatmap — Jawa Barat dan Papua merah.
│     Klik Papua → lihat 3 komoditas naik bersamaan.
│
├─ 5. TANYA AI ASSISTANT
│     Buka AI Chat.
│     Ketik: "Kenapa cabai rawit naik tajam minggu ini?"
│
│     AI menjawab:
│     "Berdasarkan data PIHPS BI (3-10 Maret 2026), harga cabai rawit
│      nasional naik 12% dalam 7 hari, dari Rp 76.000 ke Rp 85.000/kg.
│      Kenaikan tertinggi di Jawa Barat (+15%), Jawa Timur (+11%),
│      dan Lampung (+10%).
│
│      Faktor yang teridentifikasi dari data:
│      - Mendekati periode Ramadan (mulai ~22 Maret 2026)
│      - Curah hujan di atas normal di sentra produksi Jawa Barat
│        (BMKG, 8 Maret)
│
│      Sumber: PIHPS BI, BMKG | Periode: 3-10 Maret 2026"
│
│     User lanjut bertanya: "Wilayah mana lagi yang perlu diwaspadai?"
│
│     AI menjawab:
│     "Berdasarkan risk score per 10 Maret 2026, wilayah dengan
│      kategori risiko TINGGI:
│      1. Papua — 3 komoditas naik bersamaan (beras +5%, telur +7%, gula +4%)
│      2. Maluku — beras dan minyak goreng volatilitas tinggi
│      3. NTT — bawang merah deviasi 25% di atas median nasional
│
│      Sumber: PIHPS BI, analisis internal | Periode: 10 Maret 2026"
│
├─ 6. AMBIL KEPUTUSAN
│     User sekarang punya gambaran:
│     - Cabai rawit = prioritas nasional (Ramadan + cuaca)
│     - Papua & Maluku = prioritas regional (multi-komoditas)
│     - Perlu koordinasi: distribusi stok ke wilayah timur
│
└─ 09:15 — Selesai review. 15 menit untuk insight yang dulu butuh 2 jam.
```

---

## 17. Contoh Output Insight Otomatis

### Insight Harian (auto-generated setiap pagi)

```markdown
📊 INSIGHT HARIAN — Senin, 10 Maret 2026

RINGKASAN:
Tekanan harga pangan meningkat menjelang Ramadan. Cabai rawit menjadi
komoditas dengan kenaikan tertinggi minggu ini (+12%), diikuti bawang
merah (+7%) dan telur ayam ras (+4%).

KOMODITAS PERLU DIPERHATIKAN:
• Cabai rawit: Rp 85.000/kg (+12% w/w). Kenaikan terjadi di 28 dari
  34 provinsi. Tertinggi: Jawa Barat Rp 95.000/kg.
• Bawang merah: Rp 42.000/kg (+7% w/w). Volatilitas tinggi 2 minggu
  berturut-turut (CV 18.3%).
• Telur ayam ras: Rp 28.500/kg (+4% w/w). Kenaikan merata nasional.

WILAYAH PERLU DIPERHATIKAN:
• Papua: 3 komoditas naik bersamaan — risk score TINGGI (78/100)
• Maluku: beras dan minyak goreng volatilitas tinggi
• Jawa Barat: harga cabai rawit 15% di atas median nasional

KONTEKS:
• Ramadan diperkirakan mulai ~22 Maret 2026
• Curah hujan di atas normal di Jawa Barat dan Jawa Tengah (BMKG)
• Kurs USD/IDR stabil di Rp 15.850 (-0.1% w/w)

Sumber: PIHPS BI, BPS, BMKG, BI JISDOR
Periode data: 3–10 Maret 2026
```

### Insight Mingguan (auto-generated setiap Senin)

```markdown
📊 RINGKASAN MINGGUAN — 3-10 Maret 2026

HEADLINE:
Inflasi pangan Februari 2026 tercatat 0.42% (MtM), dengan YoY di 5.21%.
Tekanan meningkat di minggu pertama Maret, terutama dari kelompok
bumbu dan sayuran.

PERFORMA KOMODITAS (minggu ini vs minggu lalu):
┌─────────────────┬───────────┬────────┬──────────┐
│ Komoditas       │ Harga/kg  │ Δ w/w  │ Status   │
├─────────────────┼───────────┼────────┼──────────┤
│ Cabai rawit     │ 85.000    │ +12.0% │ 🔴 Alert │
│ Bawang merah    │ 42.000    │ +7.0%  │ 🟡 Watch │
│ Telur ayam ras  │ 28.500    │ +4.0%  │ 🟡 Watch │
│ Gula pasir      │ 17.200    │ +2.0%  │ Normal   │
│ Beras           │ 14.850    │ +1.2%  │ Normal   │
│ Minyak goreng   │ 18.100    │ +0.5%  │ Normal   │
│ Bawang putih    │ 38.000    │ -0.3%  │ Normal   │
│ Cabai merah     │ 55.000    │ -1.2%  │ Normal   │
└─────────────────┴───────────┴────────┴──────────┘

TOP 5 WILAYAH TERTEKAN:
1. Papua (avg +8.2%) — multi-komoditas, risiko distribusi
2. Maluku (+6.1%) — volatilitas beras dan minyak goreng
3. NTT (+5.3%) — deviasi bawang merah tinggi
4. Sulawesi Utara (+4.8%) — cabai rawit dan telur
5. Kalimantan Timur (+4.0%) — beras di atas rata-rata

PERBANDINGAN VS MINGGU LALU:
• Jumlah alert naik: 3 → 6 (+100%)
• Rata-rata kenaikan harga nasional: 1.8% → 3.2%
• Komoditas stabil: minyak goreng, bawang putih, cabai merah

OUTLOOK MINGGU DEPAN:
• Ramadan mendekati — historis: cabai, bawang merah, telur naik 10-20%
• Panen raya beras sedang berlangsung — tekanan harga beras terbatas
• Perhatikan: Jawa Barat (curah hujan tinggi mempengaruhi pasokan cabai)

Sumber: PIHPS BI, BPS, BMKG, BI JISDOR
Periode analisis: 3–10 Maret 2026
Data inflasi terakhir: Februari 2026 (BPS)
```

---

## 18. Rekomendasi Strategi Demo/Pilot

### Tahap Demo

#### Demo 1 — Internal (Minggu 5)
- **Audience:** Tim internal + stakeholder kunci
- **Fokus:** Data pipeline berjalan, dashboard overview, angka valid
- **Goal:** Validasi bahwa data benar dan UI intuitif
- **Format:** 20 menit walkthrough + 10 menit feedback

#### Demo 2 — MVP Feature Complete (Minggu 8)
- **Audience:** Tim + stakeholder + calon user pilot
- **Fokus:** Full flow: Overview → Komoditas → Peta → Alert → AI Chat
- **Goal:** Buy-in untuk pilot
- **Format:** 30 menit live demo + 15 menit Q&A

#### Demo 3 — Pilot Kickoff (Minggu 10)
- **Audience:** User pilot (5-10 orang)
- **Fokus:** Hands-on user testing
- **Goal:** Collect feedback, identifikasi bug
- **Format:** 15 menit intro + 30 menit hands-on + 15 menit feedback

### Strategi Pilot

| Aspek | Rekomendasi |
|-------|-------------|
| **Durasi pilot** | 2 minggu |
| **Jumlah user** | 5-10 orang dari berbagai persona |
| **Onboarding** | 1 sesi walkthrough 30 menit |
| **Feedback** | Google Form harian (1 menit) + interview akhir |
| **Support** | Chat group dedicated untuk bug/pertanyaan |
| **Success criteria** | >80% user merasa terbantu (survey) |

### Script Demo Pitch (2 menit)

> *"Setiap minggu, tim pemantauan harga menghabiskan berjam-jam mengumpulkan data dari BPS, PIHPS, BMKG, dan sumber lainnya. Lalu menganalisis manual di spreadsheet. Hasilnya sering terlambat — tekanan harga sudah terjadi sebelum insight sampai ke pengambil kebijakan.*
>
> *Platform INFLASI mengintegrasikan 6 sumber data resmi secara otomatis, memberikan alert dini saat ada anomali harga, dan memiliki AI assistant yang bisa menjawab pertanyaan langsung dari data.*
>
> *Apa yang dulu butuh 2 jam, sekarang bisa didapat dalam 5 menit. Mari saya tunjukkan."*

### Tips Demo

1. **Mulai dari masalah nyata:** "Kemarin cabai rawit naik 12%. Bagaimana kita mendeteksinya?"
2. **Gunakan data real** (bukan dummy) — ini yang paling meyakinkan stakeholder
3. **Tunjukkan AI assistant terakhir** — ini wow factor
4. **Siapkan pertanyaan yang pasti bisa dijawab AI** untuk demo
5. **Akui keterbatasan** — "Di MVP ini belum ada forecasting, tapi..."
6. **Akhiri dengan impact:** "Bayangkan jika alert ini datang 3 hari lebih awal ke Gubernur."

---

## Lampiran: Daftar Pertanyaan Utama yang Wajib Dijawab Sistem

| # | Pertanyaan | Dijawab Oleh |
|---|-----------|-------------|
| 1 | Berapa inflasi pangan bulan ini? | Dashboard Overview |
| 2 | Komoditas apa yang paling naik minggu ini? | Dashboard + AI |
| 3 | Wilayah mana yang tekanan harganya paling tinggi? | Peta + AI |
| 4 | Apakah ada komoditas yang perlu diwaspadai? | Alert Center + AI |
| 5 | Bagaimana tren harga beras 3 bulan terakhir? | Komoditas + AI |
| 6 | Kenapa harga cabai rawit naik? | AI (dengan data cuaca + musiman) |
| 7 | Bandingkan harga di wilayah A vs B | AI |
| 8 | Apa yang berubah dari minggu lalu? | Insight Mingguan + AI |
| 9 | Apakah kenaikan ini terkait musiman? | AI (dengan dim_calendar) |
| 10 | Berapa harga komoditas X di wilayah Y? | Dashboard + AI |

---

*Dokumen ini adalah blueprint MVP yang siap dijadikan acuan eksekusi. Semua keputusan arsitektur, prioritas, dan timeline di atas bersifat rekomendasi dan dapat disesuaikan berdasarkan constraint spesifik tim dan stakeholder.*
