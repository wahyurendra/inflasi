"""
BMKG Weather Data Pipeline.

Mengambil data cuaca dari BMKG Open Data API (prakiraan cuaca per provinsi).
Menyimpan ke tabel fact_climate.

Sumber: https://data.bmkg.go.id/DataMKG/MEWS/DigitalForecast/
Format: XML (DigitalForecast per provinsi)
"""

import logging
import asyncio
from datetime import date, timedelta
from typing import Any
from xml.etree import ElementTree as ET

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
        """Fetch weather XML data from BMKG for all provinces."""
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
                # Small delay to be polite to BMKG servers
                await asyncio.sleep(0.2)
        return records

    async def validate(self, raw: Any) -> bool:
        if not raw:
            logger.warning("No BMKG data fetched")
            return False
        valid = sum(1 for r in raw if r.get("xml_content"))
        logger.info(f"BMKG: Got XML data from {valid}/{len(BMKG_PROVINCE_FILES)} provinces")
        return valid >= 10  # at least 10 provinces

    async def transform(self, raw: Any) -> Any:
        """Parse XML and extract temperature + rainfall averages per province."""
        clean = []
        for record in raw:
            try:
                xml_text = record["xml_content"]

                # Parse using proper XML parser
                avg_temp = self._extract_avg_param_xml(xml_text, "t")
                avg_humidity = self._extract_avg_param_xml(xml_text, "hu")
                max_rainfall = self._extract_max_rainfall_xml(xml_text)

                warning = classify_warning(max_rainfall) if max_rainfall else "normal"
                anomali = None
                if max_rainfall and max_rainfall > RAINFALL_THRESHOLDS["waspada"]:
                    anomali = f"Curah hujan {max_rainfall:.0f}mm"

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

    def _extract_avg_param_xml(self, xml_text: str, param_id: str) -> float | None:
        """
        Extract average value for a parameter from BMKG DigitalForecast XML.
        Uses proper XML parsing via ElementTree.

        BMKG XML structure:
        <data>
          <forecast>
            <area ...>
              <parameter id="t" description="Temperature" type="hourly">
                <timerange ...>
                  <value unit="C">28</value>
                </timerange>
              </parameter>
            </area>
          </forecast>
        </data>
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return None

        values = []
        # Find all parameter elements with matching id
        for param in root.iter("parameter"):
            if param.get("id") == param_id:
                for timerange in param.iter("timerange"):
                    for value_elem in timerange.iter("value"):
                        text = value_elem.text
                        if text and text.strip():
                            try:
                                values.append(float(text.strip()))
                            except ValueError:
                                continue

        if not values:
            return None

        return round(sum(values) / len(values), 2)

    def _extract_max_rainfall_xml(self, xml_text: str) -> float:
        """
        Extract maximum rainfall from BMKG XML.
        Looks for weather code parameter and maps to estimated rainfall.
        BMKG weather codes: 0=clear, 1=partly cloudy, 2=cloudy, 3=overcast,
        4=smoke/haze, 5=fog, 60=light rain, 61=rain, 63=heavy rain, 95=thunderstorm
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return 0.0

        # Map weather codes to estimated rainfall (mm)
        weather_rainfall = {
            0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 10: 0,
            60: 5, 61: 15, 63: 40, 80: 20, 95: 60, 97: 80,
        }

        max_rain = 0.0

        # Look for weather parameter
        for param in root.iter("parameter"):
            pid = param.get("id", "")
            if pid in ("weather", "ws"):
                for timerange in param.iter("timerange"):
                    for value_elem in timerange.iter("value"):
                        text = value_elem.text
                        if text and text.strip():
                            try:
                                code = int(float(text.strip()))
                                rain = weather_rainfall.get(code, 0)
                                max_rain = max(max_rain, rain)
                            except ValueError:
                                continue

        # Also check humidity as supplementary signal
        if max_rain == 0:
            humidity = self._extract_avg_param_xml(xml_text, "hu")
            if humidity and humidity > 90:
                max_rain = (humidity - 85) * 2  # rough proxy

        return max_rain

    async def load(self, clean: Any) -> None:
        """Upsert weather data to fact_climate."""
        loaded = 0
        for record in clean:
            # Lookup region_id from kode_bps
            result = await self.db.execute(
                text("SELECT id FROM dim_region WHERE kode_wilayah = :kode"),
                {"kode": record["kode_bps"]},
            )
            row = result.fetchone()
            if not row:
                logger.debug(f"BMKG: region not found for kode_bps={record['kode_bps']}")
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
            loaded += 1
        await self.db.commit()
        logger.info(f"BMKG: Loaded {loaded} province records")
