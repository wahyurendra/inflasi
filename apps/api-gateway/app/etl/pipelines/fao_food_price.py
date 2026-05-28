"""
Pipeline: FAO Food Price Index

Sumber:
  1. FAO official data portal (CSV bulk download)
     https://www.fao.org/worldfoodsituation/foodpricesindex/en/
  2. Fallback: World Bank (FOOD_G_T indicator)
Frekuensi: Bulanan
Data: Indeks harga pangan global (overall, cereals, vegetable oil, dairy, meat, sugar)
"""

import logging
import csv
import io
from datetime import date
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# FAO official CSV for food price index data
# This is the actual downloadable CSV from FAO's website
FAO_CSV_URL = "https://www.fao.org/fileadmin/templates/worldfood/Reports_and_docs/Food_price_indices_data_jul14.csv"

# Alternative: FAO FPMA Tool API
FPMA_API_URL = "https://fpma.fao.org/giews/fpmat4/api"


class FAOFoodPricePipeline:
    """Pipeline untuk FAO Food Price Index."""

    name = "fao_food_price"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; InflasiBot/1.0)"},
        )

    async def run(self) -> int:
        """Run full pipeline. Returns count of records loaded."""
        logger.info(f"[{self.name}] Starting FAO Food Price Index pipeline")

        try:
            raw = await self._fetch_data()
            if not raw:
                logger.warning(f"[{self.name}] No data fetched")
                return 0

            count = await self._load(raw)
            logger.info(f"[{self.name}] Loaded {count} records")
            return count
        except Exception as e:
            logger.error(f"[{self.name}] Pipeline failed: {e}")
            raise
        finally:
            await self.client.aclose()

    async def _fetch_data(self) -> list[dict]:
        """
        Fetch FAO food price index data.
        Tries FAO CSV first, then World Bank as fallback.
        """
        # Primary: FAO official CSV
        try:
            csv_data = await self._fetch_from_fao_csv()
            if csv_data:
                logger.info(f"[{self.name}] Got {len(csv_data)} records from FAO CSV")
                return csv_data
        except Exception as e:
            logger.warning(f"[{self.name}] FAO CSV failed: {e}")

        # Fallback: World Bank API
        try:
            wb_data = await self._fetch_from_worldbank()
            if wb_data:
                logger.info(f"[{self.name}] Got {len(wb_data)} records from World Bank")
                return wb_data
        except Exception as e:
            logger.warning(f"[{self.name}] World Bank API failed: {e}")

        return []

    async def _fetch_from_fao_csv(self) -> list[dict]:
        """
        Fetch from FAO official CSV data.
        The CSV contains monthly indices with columns for each food group.
        """
        resp = await self.client.get(FAO_CSV_URL)
        if resp.status_code != 200:
            logger.warning(f"[{self.name}] FAO CSV HTTP {resp.status_code}")
            return []

        content = resp.text
        if not content or len(content) < 100:
            return []

        # Try different CSV dialects (FAO uses various formats)
        results = []

        # Try standard CSV parsing
        try:
            reader = csv.DictReader(io.StringIO(content))
            headers = reader.fieldnames or []
            logger.debug(f"[{self.name}] FAO CSV headers: {headers}")

            for row in reader:
                try:
                    record = self._parse_fao_row(row)
                    if record:
                        results.append(record)
                except (ValueError, TypeError) as e:
                    logger.debug(f"[{self.name}] Skip row: {e}")
                    continue
        except csv.Error:
            # Try tab-separated
            reader = csv.DictReader(io.StringIO(content), delimiter="\t")
            for row in reader:
                try:
                    record = self._parse_fao_row(row)
                    if record:
                        results.append(record)
                except (ValueError, TypeError):
                    continue

        return results

    def _parse_fao_row(self, row: dict) -> dict | None:
        """Parse a single FAO CSV row into our format."""
        # Try various column name patterns FAO uses
        periode = (
            row.get("Date") or row.get("date") or row.get("Month")
            or row.get("Tanggal") or row.get("Period") or row.get("period")
        )
        if not periode:
            return None

        overall = self._safe_float(
            row.get("Food Price Index") or row.get("FPI")
            or row.get("Food") or row.get("food_price_index")
            or row.get("Food price index")
        )
        if overall is None:
            return None

        return {
            "periode": periode,
            "index_overall": overall,
            "index_cereals": self._safe_float(
                row.get("Cereals") or row.get("Cereal Price Index")
                or row.get("cereals") or row.get("Cereal price index")
            ),
            "index_veg_oil": self._safe_float(
                row.get("Vegetable Oils") or row.get("Oils")
                or row.get("vegetable_oils") or row.get("Vegetable oils")
            ),
            "index_dairy": self._safe_float(
                row.get("Dairy") or row.get("Dairy Price Index")
                or row.get("dairy") or row.get("Dairy price index")
            ),
            "index_meat": self._safe_float(
                row.get("Meat") or row.get("Meat Price Index")
                or row.get("meat") or row.get("Meat price index")
            ),
            "index_sugar": self._safe_float(
                row.get("Sugar") or row.get("Sugar Price Index")
                or row.get("sugar") or row.get("Sugar price index")
            ),
        }

    def _safe_float(self, val) -> float | None:
        if val is None or str(val).strip() in ("", "-", "n/a", "N/A"):
            return None
        try:
            return float(str(val).replace(",", "").strip())
        except (ValueError, TypeError):
            return None

    async def _fetch_from_worldbank(self) -> list[dict]:
        """
        Fetch food price index from World Bank API.
        Uses GEM Commodities (source=6) FOOD indicator.
        """
        # Try multiple indicator codes
        indicators = ["FOOD_G_T", "AG.PRD.FOOD.XD"]

        for indicator in indicators:
            url = f"https://api.worldbank.org/v2/country/WLD/indicator/{indicator}"
            params = {
                "format": "json",
                "per_page": "120",
                "date": "2020:2026",
                "source": "6",
            }

            resp = await self.client.get(url, params=params)
            if resp.status_code != 200:
                # Try without source filter
                params.pop("source")
                resp = await self.client.get(url, params=params)

            if resp.status_code != 200:
                continue

            try:
                payload = resp.json()
            except Exception:
                continue

            if not payload or len(payload) < 2 or not payload[1]:
                continue

            records = payload[1]
            results = []
            for rec in records:
                val = rec.get("value")
                if val is None:
                    continue
                date_str = str(rec.get("date", ""))

                # Parse various WB date formats
                if "M" in date_str:
                    parts = date_str.split("M")
                    if len(parts) == 2:
                        periode_str = f"{parts[0]}-{parts[1].zfill(2)}-01"
                    else:
                        continue
                elif len(date_str) == 4:
                    periode_str = f"{date_str}-01-01"
                else:
                    continue

                results.append({
                    "periode": periode_str,
                    "index_overall": float(val),
                    "index_cereals": None,
                    "index_veg_oil": None,
                    "index_dairy": None,
                    "index_meat": None,
                    "index_sugar": None,
                })

            if results:
                return results

        return []

    async def _load(self, data: list[dict]) -> int:
        """Upsert to ext_fao_food_price."""
        count = 0
        for row in data:
            try:
                periode = row["periode"]
                if isinstance(periode, str):
                    periode = self._parse_date(periode)
                if periode is None:
                    continue

                await self.db.execute(
                    text("""
                        INSERT INTO ext_fao_food_price
                            (periode, index_overall, index_cereals, index_veg_oil, index_dairy, index_meat, index_sugar)
                        VALUES
                            (:periode, :index_overall, :index_cereals, :index_veg_oil, :index_dairy, :index_meat, :index_sugar)
                        ON CONFLICT (periode)
                        DO UPDATE SET
                            index_overall = EXCLUDED.index_overall,
                            index_cereals = COALESCE(EXCLUDED.index_cereals, ext_fao_food_price.index_cereals),
                            index_veg_oil = COALESCE(EXCLUDED.index_veg_oil, ext_fao_food_price.index_veg_oil),
                            index_dairy   = COALESCE(EXCLUDED.index_dairy, ext_fao_food_price.index_dairy),
                            index_meat    = COALESCE(EXCLUDED.index_meat, ext_fao_food_price.index_meat),
                            index_sugar   = COALESCE(EXCLUDED.index_sugar, ext_fao_food_price.index_sugar)
                    """),
                    {
                        "periode": periode,
                        "index_overall": row.get("index_overall"),
                        "index_cereals": row.get("index_cereals"),
                        "index_veg_oil": row.get("index_veg_oil"),
                        "index_dairy": row.get("index_dairy"),
                        "index_meat": row.get("index_meat"),
                        "index_sugar": row.get("index_sugar"),
                    },
                )
                count += 1
            except Exception as e:
                logger.warning(f"[{self.name}] Skip row: {e}")

        await self.db.commit()
        return count

    def _parse_date(self, s: str) -> date | None:
        """Parse various date string formats to date object."""
        s = s.strip()
        # Try ISO format: YYYY-MM-DD
        try:
            return date.fromisoformat(s)
        except ValueError:
            pass
        # Try YYYY-MM
        if len(s) == 7 and "-" in s:
            try:
                return date.fromisoformat(f"{s}-01")
            except ValueError:
                pass
        # Try YYYY only
        if len(s) == 4:
            try:
                return date(int(s), 1, 1)
            except ValueError:
                pass
        # Try MM/YYYY or M/YYYY
        if "/" in s:
            parts = s.split("/")
            if len(parts) == 2:
                try:
                    month, year = int(parts[0]), int(parts[1])
                    return date(year, month, 1)
                except (ValueError, IndexError):
                    pass
        return None
