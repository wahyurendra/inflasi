"""
Pipeline: FAO Food Price Index

Sumber: https://www.fao.org/worldfoodsituation/foodpricesindex
Frekuensi: Bulanan
Data: Indeks harga pangan global (overall, cereals, vegetable oil, dairy, meat, sugar)

API: FAO FPMA API (Food Price Monitoring and Analysis)
  GET https://fpma.fao.org/giews/fpmat4/#/dashboard/tool/international
  Bulk CSV: https://www.fao.org/faostat/en/#data/CP (FAOSTAT Commodity Prices)
"""

import logging
from datetime import date
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# FAO FAOSTAT bulk CSV URL for food price index
# Alternative: scrape from FAO data portal
FAO_DATA_URL = "https://www.fao.org/fileadmin/templates/worldfood/Reports_and_docs/Food_price_indices_data_jul14.csv"


class FAOFoodPricePipeline:
    """Pipeline untuk FAO Food Price Index."""

    name = "fao_food_price"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = httpx.AsyncClient(
            timeout=30.0,
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
        Uses World Bank API as primary source (more reliable for programmatic access).
        """
        results = []

        # Use World Bank API for FAO-related food price data
        # AG.PRD.FOOD.XD = Food price index
        try:
            wb_data = await self._fetch_from_worldbank()
            if wb_data:
                return wb_data
        except Exception as e:
            logger.warning(f"[{self.name}] World Bank API failed: {e}")

        # Fallback: try FAO CSV
        try:
            csv_data = await self._fetch_from_fao_csv()
            if csv_data:
                return csv_data
        except Exception as e:
            logger.warning(f"[{self.name}] FAO CSV failed: {e}")

        return results

    async def _fetch_from_worldbank(self) -> list[dict]:
        """Fetch food price index from World Bank API."""
        # World Bank commodity price data (Pink Sheet)
        url = "https://api.worldbank.org/v2/country/WLD/indicator/FOOD_G_T"
        params = {
            "format": "json",
            "per_page": "120",  # 10 years monthly
            "date": "2020:2026",
        }

        resp = await self.client.get(url, params=params)
        if resp.status_code != 200:
            return []

        payload = resp.json()
        if not payload or len(payload) < 2:
            return []

        records = payload[1] or []
        results = []
        for rec in records:
            val = rec.get("value")
            if val is None:
                continue
            year = rec.get("date", "")
            # World Bank returns annual data for this indicator
            results.append({
                "periode": f"{year}-01-01",
                "index_overall": float(val),
            })

        return results

    async def _fetch_from_fao_csv(self) -> list[dict]:
        """Fetch from FAO CSV data."""
        resp = await self.client.get(FAO_DATA_URL)
        if resp.status_code != 200:
            return []

        import csv
        import io

        reader = csv.DictReader(io.StringIO(resp.text))
        results = []
        for row in reader:
            try:
                # FAO CSV format varies, try common column names
                periode = row.get("Date") or row.get("date") or row.get("Month")
                overall = row.get("Food Price Index") or row.get("FPI") or row.get("Food")
                cereals = row.get("Cereals") or row.get("Cereal Price Index")
                veg_oil = row.get("Vegetable Oils") or row.get("Oils")
                dairy = row.get("Dairy") or row.get("Dairy Price Index")
                meat = row.get("Meat") or row.get("Meat Price Index")
                sugar = row.get("Sugar") or row.get("Sugar Price Index")

                if not periode or not overall:
                    continue

                results.append({
                    "periode": periode,
                    "index_overall": float(str(overall).replace(",", "")),
                    "index_cereals": float(str(cereals).replace(",", "")) if cereals else None,
                    "index_veg_oil": float(str(veg_oil).replace(",", "")) if veg_oil else None,
                    "index_dairy": float(str(dairy).replace(",", "")) if dairy else None,
                    "index_meat": float(str(meat).replace(",", "")) if meat else None,
                    "index_sugar": float(str(sugar).replace(",", "")) if sugar else None,
                })
            except (ValueError, TypeError):
                continue

        return results

    async def _load(self, data: list[dict]) -> int:
        """Upsert to ext_fao_food_price."""
        count = 0
        for row in data:
            try:
                periode = row["periode"]
                if isinstance(periode, str):
                    if len(periode) == 4:
                        periode = f"{periode}-01-01"
                    periode = date.fromisoformat(periode)

                await self.db.execute(
                    text("""
                        INSERT INTO ext_fao_food_price (periode, index_overall, index_cereals, index_veg_oil, index_dairy, index_meat, index_sugar)
                        VALUES (:periode, :index_overall, :index_cereals, :index_veg_oil, :index_dairy, :index_meat, :index_sugar)
                        ON CONFLICT (periode)
                        DO UPDATE SET index_overall = EXCLUDED.index_overall,
                                      index_cereals = EXCLUDED.index_cereals,
                                      index_veg_oil = EXCLUDED.index_veg_oil,
                                      index_dairy = EXCLUDED.index_dairy,
                                      index_meat = EXCLUDED.index_meat,
                                      index_sugar = EXCLUDED.index_sugar
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
