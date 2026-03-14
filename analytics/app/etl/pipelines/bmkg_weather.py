"""
BMKG Weather Data Pipeline.

Mengambil data cuaca dari BMKG Open Data API (prakiraan cuaca per provinsi).
Menyimpan ke tabel fact_climate.
"""

import logging
from datetime import date, timedelta
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.base import DataPipeline

logger = logging.getLogger(__name__)

# BMKG Data MKG endpoint (XML prakiraan cuaca)
BMKG_BASE_URL = "https://data.bmkg.go.id/DataMKG/MEWS/DigitalForecast"

# Mapping kode provinsi BMKG -> kode BPS
BMKG_PROVINCE_FILES = {
    "Aceh": ("DigitalForecast-Aceh.xml", "11"),
    "SumateraUtara": ("DigitalForecast-SumateraUtara.xml", "12"),
    "SumatraBarat": ("DigitalForecast-SumatraBarat.xml", "13"),
    "Riau": ("DigitalForecast-Riau.xml", "14"),
    "Jambi": ("DigitalForecast-Jambi.xml", "15"),
    "SumateraSelatan": ("DigitalForecast-SumateraSelatan.xml", "16"),
    "Bengkulu": ("DigitalForecast-Bengkulu.xml", "17"),
    "Lampung": ("DigitalForecast-Lampung.xml", "18"),
    "BangkaBelitung": ("DigitalForecast-BangkaBelitung.xml", "19"),
    "KepulauanRiau": ("DigitalForecast-KepulauanRiau.xml", "21"),
    "DKIJakarta": ("DigitalForecast-DKIJakarta.xml", "31"),
    "JawaBarat": ("DigitalForecast-JawaBarat.xml", "32"),
    "JawaTengah": ("DigitalForecast-JawaTengah.xml", "33"),
    "DIYogyakarta": ("DigitalForecast-DIYogyakarta.xml", "34"),
    "JawaTimur": ("DigitalForecast-JawaTimur.xml", "35"),
    "Banten": ("DigitalForecast-Banten.xml", "36"),
    "Bali": ("DigitalForecast-Bali.xml", "51"),
    "NusaTenggaraBarat": ("DigitalForecast-NusaTenggaraBarat.xml", "52"),
    "NusaTenggaraTimur": ("DigitalForecast-NusaTenggaraTimur.xml", "53"),
    "KalimantanBarat": ("DigitalForecast-KalimantanBarat.xml", "61"),
    "KalimantanTengah": ("DigitalForecast-KalimantanTengah.xml", "62"),
    "KalimantanSelatan": ("DigitalForecast-KalimantanSelatan.xml", "63"),
    "KalimantanTimur": ("DigitalForecast-KalimantanTimur.xml", "64"),
    "KalimantanUtara": ("DigitalForecast-KalimantanUtara.xml", "65"),
    "SulawesiUtara": ("DigitalForecast-SulawesiUtara.xml", "71"),
    "SulawesiTengah": ("DigitalForecast-SulawesiTengah.xml", "72"),
    "SulawesiSelatan": ("DigitalForecast-SulawesiSelatan.xml", "73"),
    "SulawesiTenggara": ("DigitalForecast-SulawesiTenggara.xml", "74"),
    "Gorontalo": ("DigitalForecast-Gorontalo.xml", "75"),
    "SulawesiBarat": ("DigitalForecast-SulawesiBarat.xml", "76"),
    "Maluku": ("DigitalForecast-Maluku.xml", "81"),
    "MalukuUtara": ("DigitalForecast-MalukuUtara.xml", "82"),
    "Papua": ("DigitalForecast-Papua.xml", "91"),
    "PapuaBarat": ("DigitalForecast-PapuaBarat.xml", "92"),
}

# Rainfall thresholds (mm/day) for warning levels
RAINFALL_THRESHOLDS = {
    "normal": 20,
    "waspada": 50,
    "siaga": 100,
    "awas": 150,
}


def classify_warning(rainfall_mm: float) -> str:
    if rainfall_mm >= RAINFALL_THRESHOLDS["awas"]:
        return "awas"
    elif rainfall_mm >= RAINFALL_THRESHOLDS["siaga"]:
        return "siaga"
    elif rainfall_mm >= RAINFALL_THRESHOLDS["waspada"]:
        return "waspada"
    return "normal"


class BMKGWeatherPipeline(DataPipeline):
    name = "bmkg_weather"

    def __init__(self, db: AsyncSession, target_date: date | None = None):
        self.db = db
        self.target_date = target_date or date.today()

    async def extract(self) -> Any:
        """Fetch weather data from BMKG for all provinces."""
        records = []
        async with httpx.AsyncClient(timeout=30) as client:
            for prov_name, (filename, kode_bps) in BMKG_PROVINCE_FILES.items():
                try:
                    url = f"{BMKG_BASE_URL}/{filename}"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        records.append({
                            "province": prov_name,
                            "kode_bps": kode_bps,
                            "xml_content": resp.text,
                        })
                    else:
                        logger.warning(f"BMKG {prov_name}: HTTP {resp.status_code}")
                except Exception as e:
                    logger.warning(f"BMKG {prov_name}: {e}")
        return records

    async def validate(self, raw: Any) -> bool:
        if not raw:
            logger.warning("No BMKG data fetched")
            return False
        return len(raw) >= 10  # at least 10 provinces

    async def transform(self, raw: Any) -> Any:
        """Parse XML and extract temperature + rainfall averages per province."""
        clean = []
        for record in raw:
            try:
                xml = record["xml_content"]
                # Simple XML parsing — extract temperature and humidity values
                # BMKG XML has <parameter id="t" ...> for temperature
                # and <parameter id="hu" ...> for humidity

                avg_temp = self._extract_avg_param(xml, "t")
                avg_humidity = self._extract_avg_param(xml, "hu")
                max_rainfall = self._extract_max_rainfall(xml)

                warning = classify_warning(max_rainfall) if max_rainfall else "normal"
                anomali = f"Curah hujan {max_rainfall:.0f}mm" if max_rainfall > RAINFALL_THRESHOLDS["waspada"] else None

                clean.append({
                    "tanggal": self.target_date,
                    "kode_bps": record["kode_bps"],
                    "curah_hujan": max_rainfall,
                    "suhu_rata": avg_temp,
                    "anomali_cuaca": anomali,
                    "warning_level": warning,
                })
            except Exception as e:
                logger.warning(f"BMKG transform {record['province']}: {e}")
        return clean

    def _extract_avg_param(self, xml: str, param_id: str) -> float | None:
        """Extract average value for a parameter from BMKG XML."""
        import re
        # Find parameter block
        pattern = rf'<parameter id="{param_id}"[^>]*>(.*?)</parameter>'
        match = re.search(pattern, xml, re.DOTALL)
        if not match:
            return None
        block = match.group(1)
        # Find all <value> tags
        values = re.findall(r'<value[^>]*>(\d+\.?\d*)</value>', block)
        if not values:
            return None
        nums = [float(v) for v in values if v]
        return sum(nums) / len(nums) if nums else None

    def _extract_max_rainfall(self, xml: str) -> float:
        """Extract maximum rainfall from BMKG XML weather parameter."""
        import re
        # Look for weather/precipitation parameter
        pattern = r'<parameter id="(?:weather|ws)"[^>]*>(.*?)</parameter>'
        match = re.search(pattern, xml, re.DOTALL)
        if match:
            values = re.findall(r'<value[^>]*>(\d+\.?\d*)</value>', match.group(1))
            if values:
                return max(float(v) for v in values)

        # Fallback: look for humidity as proxy (high humidity = likely rain)
        humidity = self._extract_avg_param(xml, "hu")
        if humidity and humidity > 85:
            return (humidity - 85) * 3  # rough proxy
        return 0.0

    async def load(self, clean: Any) -> None:
        """Upsert weather data to fact_climate."""
        for record in clean:
            # Lookup region_id from kode_bps
            result = await self.db.execute(
                text("SELECT id FROM dim_region WHERE kode_wilayah = :kode"),
                {"kode": record["kode_bps"]},
            )
            row = result.fetchone()
            if not row:
                continue

            await self.db.execute(
                text("""
                    INSERT INTO fact_climate
                        (tanggal, region_id, curah_hujan, suhu_rata, anomali_cuaca, warning_level, sumber)
                    VALUES
                        (:tanggal, :region_id, :curah_hujan, :suhu_rata, :anomali, :warning, 'BMKG')
                    ON CONFLICT (tanggal, region_id)
                    DO UPDATE SET
                        curah_hujan = EXCLUDED.curah_hujan,
                        suhu_rata = EXCLUDED.suhu_rata,
                        anomali_cuaca = EXCLUDED.anomali_cuaca,
                        warning_level = EXCLUDED.warning_level
                """),
                {
                    "tanggal": record["tanggal"],
                    "region_id": row.id,
                    "curah_hujan": record["curah_hujan"],
                    "suhu_rata": record["suhu_rata"],
                    "anomali": record["anomali_cuaca"],
                    "warning": record["warning_level"],
                },
            )
        await self.db.commit()
