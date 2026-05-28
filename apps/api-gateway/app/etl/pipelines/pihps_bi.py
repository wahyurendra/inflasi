"""
Pipeline: PIHPS BI (Pusat Informasi Harga Pangan Strategis - Bank Indonesia)

Sumber: https://www.bi.go.id/hargapangan
Frekuensi: Harian
Data: Harga pangan harian per komoditas per wilayah (pasar tradisional)

API BI (ditemukan via reverse-engineering DevExtreme DataGrid):
  GET /WebSite/TabelHarga/GetGridDataKomoditas
  GET /WebSite/TabelHarga/GetGridDataDaerah
  GET /WebSite/TabelHarga/GetRefProvince
"""

import logging
from datetime import date, timedelta
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.base import DataPipeline
from app.etl.mappings.commodity_map import normalize_commodity
from app.etl.mappings.region_map import normalize_region

logger = logging.getLogger(__name__)

BASE_URL = "https://www.bi.go.id/hargapangan/WebSite/TabelHarga"

# Mapping: category ID PIHPS → nama komoditas yang akan di-normalize
# Ambil satu variant per kategori sebagai representasi
PIHPS_CATEGORY_MAP: dict[str, str] = {
    "cat_1": "beras medium",        # Beras → ambil Medium I
    "cat_2": "daging ayam ras segar",  # Daging Ayam (tidak ada di 8 komoditas MVP, skip)
    "cat_3": "daging sapi",         # Daging Sapi (tidak ada di 8 komoditas MVP, skip)
    "cat_4": "telur ayam ras segar",  # Telur Ayam
    "cat_5": "bawang merah ukuran sedang",  # Bawang Merah
    "cat_6": "bawang putih ukuran sedang",  # Bawang Putih
    "cat_7": "cabai merah besar",   # Cabai Merah
    "cat_8": "cabai rawit merah",   # Cabai Rawit
    "cat_9": "minyak goreng curah", # Minyak Goreng
    "cat_10": "gula pasir lokal",   # Gula Pasir
}

# Hanya kategori yang ada di 8 komoditas MVP kita
MVP_CATEGORIES = ["cat_1", "cat_4", "cat_5", "cat_6", "cat_7", "cat_8", "cat_9", "cat_10"]

# Mapping province ID PIHPS BI → nama provinsi (untuk normalisasi ke kode BPS)
PIHPS_PROVINCE_NAMES: dict[int, str] = {
    1: "aceh",
    2: "sumatera utara",
    3: "sumatera barat",
    4: "riau",
    5: "kepulauan riau",
    6: "jambi",
    7: "bengkulu",
    8: "sumatera selatan",
    9: "kepulauan bangka belitung",
    10: "lampung",
    11: "banten",
    12: "jawa barat",
    13: "dki jakarta",
    14: "jawa tengah",
    15: "di yogyakarta",
    16: "jawa timur",
    17: "bali",
    18: "nusa tenggara barat",
    19: "nusa tenggara timur",
    20: "kalimantan barat",
    21: "kalimantan selatan",
    22: "kalimantan tengah",
    23: "kalimantan timur",
    24: "kalimantan utara",
    25: "gorontalo",
    26: "sulawesi selatan",
    27: "sulawesi tenggara",
    28: "sulawesi tengah",
    29: "sulawesi utara",
    30: "sulawesi barat",
    31: "maluku",
    32: "maluku utara",
    33: "papua",
    34: "papua barat",
}


class PIHPSPipeline(DataPipeline):
    """Pipeline untuk ingest data harga pangan dari PIHPS BI."""

    name = "pihps_bi"

    def __init__(self, db: AsyncSession, target_date: date | None = None):
        self.db = db
        self.target_date = target_date or date.today()
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; InflasiBot/1.0; +monitoring)",
                "Referer": "https://www.bi.go.id/hargapangan",
                "Accept": "application/json, text/plain, */*",
            },
        )

    async def extract(self) -> list[dict]:
        """
        Fetch harga pangan dari API PIHPS BI per kategori komoditas.
        Menggunakan endpoint GetGridDataKomoditas dengan province_id=0 (semua provinsi).
        Fallback ke CSV manual jika API tidak tersedia.
        """
        logger.info(f"[{self.name}] Extracting for date: {self.target_date}")

        try:
            data = await self._fetch_from_api()
            if data:
                logger.info(f"[{self.name}] Fetched {len(data)} rows from API")
                return data
        except Exception as e:
            logger.warning(f"[{self.name}] API fetch failed: {e}. Trying CSV fallback.")

        return await self._load_from_csv()

    async def _fetch_with_retry(self, url: str, params: dict, max_retries: int = 3) -> dict:
        """HTTP GET dengan retry exponential backoff."""
        import asyncio
        last_err = None
        for attempt in range(max_retries):
            try:
                resp = await self.client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_err = e
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.debug(f"[{self.name}] Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                    await asyncio.sleep(wait)
        raise last_err  # type: ignore

    async def _fetch_from_api(self) -> list[dict]:
        """
        Fetch data dari API PIHPS BI.
        - Nasional: GetGridDataKomoditas dengan province_id=0 (8 kategori)
        - Provinsi: GetVectorMapData per komoditas (semua 34 provinsi sekaligus)
        """
        import asyncio
        date_str = self.target_date.strftime("%Y-%m-%d")
        all_rows: list[dict] = []

        # 1. Fetch data nasional (8 requests)
        for cat_id in MVP_CATEGORIES:
            commodity_name = PIHPS_CATEGORY_MAP[cat_id]
            try:
                rows = await self._fetch_category(cat_id, date_str, commodity_name)
                all_rows.extend(rows)
                logger.debug(f"[{self.name}] Nasional {cat_id}: {len(rows)} rows")
            except Exception as e:
                logger.warning(f"[{self.name}] Failed nasional {cat_id}: {e}")

        # 2. Fetch data per provinsi via GetVectorMapData (8 requests, dapat 34 provinsi)
        # Mapping: cat_id → com_id untuk GetVectorMapData
        cat_to_com = {
            "cat_1": "com_3",   # Beras Medium I
            "cat_4": "com_10",  # Telur Ayam Ras Segar
            "cat_5": "com_11",  # Bawang Merah Ukuran Sedang
            "cat_6": "com_12",  # Bawang Putih Ukuran Sedang
            "cat_7": "com_13",  # Cabai Merah Besar
            "cat_8": "com_16",  # Cabai Rawit Merah
            "cat_9": "com_17",  # Minyak Goreng Curah
            "cat_10": "com_21", # Gula Pasir Lokal
        }
        for cat_id in MVP_CATEGORIES:
            com_id = cat_to_com.get(cat_id)
            commodity_name = PIHPS_CATEGORY_MAP[cat_id]
            if not com_id:
                continue
            try:
                prov_rows = await self._fetch_vector_map(com_id, commodity_name)
                all_rows.extend(prov_rows)
                logger.debug(f"[{self.name}] Provinsi {cat_id}: {len(prov_rows)} rows")
            except Exception as e:
                logger.warning(f"[{self.name}] Failed provinsi {cat_id}: {e}")
            # Kecil delay untuk menghindari rate limit
            await asyncio.sleep(0.3)

        return all_rows

    async def _fetch_vector_map(self, com_id: str, commodity_name: str) -> list[dict]:
        """
        Fetch data per-provinsi via GetVectorMapData.
        Mengembalikan harga aktual per provinsi dalam satu request.
        """
        payload = await self._fetch_with_retry(
            f"{BASE_URL.replace('/TabelHarga', '')}/Home/GetVectorMapData",
            {
                "tanggal": self.target_date.strftime("%Y-%m-%d"),
                "commodity": com_id,
                "priceType": "1",
                "isPasokan": "1",
                "jenis": "1",
                "periode": "WTW",
                "provId": "0",
            },
        )

        # Response format: {"data": [{"Key": "Aceh", "Value": {"id": 1, "nilai": 30450.0, ...}}]}
        entries = payload.get("data", [])
        result = []
        for entry in entries:
            val = entry.get("Value", {})
            prov_id = val.get("id")
            nilai = val.get("nilai")

            if not prov_id or nilai is None:
                continue

            prov_name = PIHPS_PROVINCE_NAMES.get(int(prov_id))
            if not prov_name:
                continue

            try:
                price = float(nilai)
                if price <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            result.append({
                "tanggal": self.target_date.isoformat(),
                "wilayah": prov_name,
                "komoditas": commodity_name,
                "harga": price,
                "level": 1,
            })

        return result

    async def _fetch_category(self, cat_id: str, date_str: str, commodity_name: str) -> list[dict]:
        """Fetch satu kategori: nasional, satu tanggal."""
        params = {
            "price_type_id": "1",          # Pasar Tradisional
            "comcat_id": cat_id,
            "province_id": "0",            # Nasional aggregate
            "regency_id": "0",
            "showKota": "false",
            "showPasar": "false",
            "tipe_laporan": "1",           # Harian
            "start_date": date_str,
            "end_date": date_str,
        }

        payload = await self._fetch_with_retry(f"{BASE_URL}/GetGridDataKomoditas", params)

        rows_raw: list[dict] = payload.get("data", [])
        date_col = self.target_date.strftime("%-d/%-m/%Y")  # e.g. "11/3/2026"

        # Fallback: coba format tanpa leading zero
        result = []
        for row in rows_raw:
            level = row.get("level", -1)
            name = (row.get("name") or "").strip()

            # level 0 = nasional, level 1 = provinsi
            if level not in (0, 1):
                continue

            # Coba berbagai format kolom tanggal
            price_str = None
            for fmt in [date_col,
                        self.target_date.strftime("%d/%m/%Y"),
                        self.target_date.strftime("%-d/%m/%Y"),
                        self.target_date.strftime("%d/%-m/%Y")]:
                if fmt in row and row[fmt] not in (None, "-", ""):
                    price_str = row[fmt]
                    break

            if price_str is None:
                continue

            try:
                price = float(str(price_str).replace(",", "").replace(".", "").strip())
                if price <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            wilayah = "nasional" if level == 0 else name.lower()

            result.append({
                "tanggal": self.target_date.isoformat(),
                "wilayah": wilayah,
                "komoditas": commodity_name,
                "harga": price,
                "level": level,
            })

        return result

    async def _load_from_csv(self) -> list[dict]:
        """
        Fallback: load data dari file CSV.
        Format: tanggal,wilayah,komoditas,harga
        Letakkan file di: analytics/data/pihps_YYYY-MM-DD.csv
        """
        import csv
        import os

        csv_path = f"data/pihps_{self.target_date.isoformat()}.csv"
        if not os.path.exists(csv_path):
            logger.warning(f"[{self.name}] CSV file not found: {csv_path}")
            return []

        data = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    data.append({
                        "tanggal": row["tanggal"],
                        "wilayah": row["wilayah"],
                        "komoditas": row["komoditas"],
                        "harga": float(str(row["harga"]).replace(",", "")),
                        "level": 1,
                    })
                except (KeyError, ValueError) as e:
                    logger.warning(f"[{self.name}] Skipping invalid CSV row {row}: {e}")

        logger.info(f"[{self.name}] Loaded {len(data)} rows from CSV")
        return data

    async def validate(self, raw: list[dict]) -> bool:
        """Validasi data: ada data, harga wajar (Rp 100 – Rp 500.000/kg)."""
        if not raw:
            logger.error(f"[{self.name}] No data extracted")
            return False

        invalid = 0
        for row in raw:
            harga = row.get("harga", 0)
            if not (100 <= harga <= 500_000):
                logger.warning(f"[{self.name}] Price out of range: {harga} for {row.get('komoditas')} @ {row.get('wilayah')}")
                invalid += 1

            if normalize_region(row.get("wilayah", "")) is None:
                logger.warning(f"[{self.name}] Unknown region: {row.get('wilayah')}")
                invalid += 1

            if normalize_commodity(row.get("komoditas", "")) is None:
                logger.warning(f"[{self.name}] Unknown commodity: {row.get('komoditas')}")
                invalid += 1

        error_rate = invalid / (len(raw) * 3) if raw else 1.0
        if error_rate > 0.3:
            logger.error(f"[{self.name}] Too many validation errors: {error_rate:.1%}")
            return False

        logger.info(f"[{self.name}] Validation passed. Error rate: {error_rate:.1%} ({invalid} issues)")
        return True

    async def transform(self, raw: list[dict]) -> list[dict]:
        """Normalisasi wilayah dan komoditas, lookup IDs dari DB."""
        region_ids = await self._get_region_ids()
        commodity_ids = await self._get_commodity_ids()

        clean = []
        seen = set()  # deduplicate (region_id, commodity_id)

        for row in raw:
            region_code = normalize_region(row["wilayah"])
            commodity_code = normalize_commodity(row["komoditas"])

            if region_code is None or commodity_code is None:
                continue

            region_id = region_ids.get(region_code)
            commodity_id = commodity_ids.get(commodity_code)

            if region_id is None or commodity_id is None:
                continue

            key = (region_id, commodity_id)
            if key in seen:
                continue  # skip duplikat (misal ada beberapa level untuk wilayah yang sama)
            seen.add(key)

            clean.append({
                "tanggal": self.target_date,
                "region_id": region_id,
                "commodity_id": commodity_id,
                "harga": row["harga"],
                "sumber": "PIHPS_BI",
            })

        logger.info(f"[{self.name}] Transformed {len(raw)} → {len(clean)} clean records")
        return clean

    async def load(self, clean: list[dict]) -> None:
        """Upsert ke fact_price_daily, lalu update perubahan harga."""
        if not clean:
            logger.warning(f"[{self.name}] No records to load")
            return

        for row in clean:
            await self.db.execute(
                text("""
                    INSERT INTO fact_price_daily (tanggal, region_id, commodity_id, harga, sumber)
                    VALUES (:tanggal, :region_id, :commodity_id, :harga, :sumber)
                    ON CONFLICT (tanggal, region_id, commodity_id)
                    DO UPDATE SET harga = EXCLUDED.harga, sumber = EXCLUDED.sumber
                """),
                row,
            )
        await self.db.commit()
        logger.info(f"[{self.name}] Loaded {len(clean)} records for {self.target_date}")

        # Update price changes (harian, mingguan, bulanan)
        await self._update_price_changes()

    async def _update_price_changes(self) -> None:
        """Hitung dan update perubahan harga harian/mingguan/bulanan."""
        await self.db.execute(text("""
            UPDATE fact_price_daily fpd
            SET perubahan_harian = CASE
                WHEN prev.harga > 0
                THEN ROUND(((fpd.harga - prev.harga) / prev.harga * 100)::numeric, 4)
                ELSE NULL
            END
            FROM (
                SELECT commodity_id, region_id, tanggal, harga,
                    LEAD(tanggal) OVER (PARTITION BY commodity_id, region_id ORDER BY tanggal) AS next_date
                FROM fact_price_daily
            ) prev
            WHERE fpd.commodity_id = prev.commodity_id
            AND fpd.region_id = prev.region_id
            AND fpd.tanggal = prev.next_date
            AND fpd.tanggal = :tanggal
        """), {"tanggal": self.target_date})

        await self.db.execute(text("""
            UPDATE fact_price_daily fpd
            SET perubahan_mingguan = CASE
                WHEN w7.harga > 0
                THEN ROUND(((fpd.harga - w7.harga) / w7.harga * 100)::numeric, 4)
                ELSE NULL
            END
            FROM fact_price_daily w7
            WHERE fpd.commodity_id = w7.commodity_id
            AND fpd.region_id = w7.region_id
            AND w7.tanggal = fpd.tanggal - INTERVAL '7 days'
            AND fpd.tanggal = :tanggal
        """), {"tanggal": self.target_date})

        await self.db.execute(text("""
            UPDATE fact_price_daily fpd
            SET perubahan_bulanan = CASE
                WHEN m30.harga > 0
                THEN ROUND(((fpd.harga - m30.harga) / m30.harga * 100)::numeric, 4)
                ELSE NULL
            END
            FROM fact_price_daily m30
            WHERE fpd.commodity_id = m30.commodity_id
            AND fpd.region_id = m30.region_id
            AND m30.tanggal = fpd.tanggal - INTERVAL '30 days'
            AND fpd.tanggal = :tanggal
        """), {"tanggal": self.target_date})

        await self.db.commit()
        logger.info(f"[{self.name}] Price changes updated for {self.target_date}")

    async def _get_region_ids(self) -> dict[str, int]:
        result = await self.db.execute(text("SELECT id, kode_wilayah FROM dim_region"))
        return {row.kode_wilayah: row.id for row in result.fetchall()}

    async def _get_commodity_ids(self) -> dict[str, int]:
        result = await self.db.execute(text("SELECT id, kode_komoditas FROM dim_commodity"))
        return {row.kode_komoditas: row.id for row in result.fetchall()}

    async def close(self):
        await self.client.aclose()
