"""
Pipeline: Global Commodity Prices (World Bank Pink Sheet + alternatives)

Data:
  - Rice, wheat, corn (cereals)
  - Palm oil, soybean oil (vegetable oils)
  - Sugar
  - Urea (fertilizer)
  - Crude oil (Brent)

Sumber:
  - World Bank GEM Commodities API (source=6)
    https://api.worldbank.org/v2/sources/6/indicators
  - Fallback: World Bank bulk CSV (Pink Sheet)
"""

import logging
import asyncio
from datetime import date, timedelta

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# World Bank GEM Commodity indicators (source 6)
# Reference: https://api.worldbank.org/v2/sources/6/indicators?format=json
WB_INDICATORS = {
    "RICE_05": ("rice", "USD/mt"),
    "WHEAT_US_HRW": ("wheat", "USD/mt"),
    "MAIZE": ("corn", "USD/mt"),
    "PALM_OIL": ("palm_oil", "USD/mt"),
    "SOYBEAN_OIL": ("soybean_oil", "USD/mt"),
    "SUGAR_WLD": ("sugar", "USD/kg"),
    "UREA_EE_BULK": ("urea", "USD/mt"),
    "CRUDE_BRENT": ("crude_oil_brent", "USD/bbl"),
}


class CommodityGlobalPipeline:
    """Pipeline untuk harga komoditas global (World Bank Pink Sheet)."""

    name = "commodity_global"

    def __init__(self, db: AsyncSession, year_start: int = 2023):
        self.db = db
        self.year_start = year_start
        self.year_end = date.today().year
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def run(self) -> int:
        logger.info(f"[{self.name}] Fetching {self.year_start}-{self.year_end}")
        total = 0

        try:
            for wb_code, (commodity, unit) in WB_INDICATORS.items():
                try:
                    data = await self._fetch_indicator(wb_code, commodity, unit)
                    if data:
                        count = await self._load(data)
                        total += count
                        logger.debug(f"[{self.name}] {commodity}: {count} records")
                    else:
                        logger.warning(f"[{self.name}] No data for {commodity} ({wb_code})")
                except Exception as e:
                    logger.warning(f"[{self.name}] Failed {commodity}: {e}")
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)

            logger.info(f"[{self.name}] Total loaded: {total} records")
            return total
        finally:
            await self.client.aclose()

    async def _fetch_indicator(self, wb_code: str, commodity: str, unit: str) -> list[dict]:
        """
        Fetch satu indikator dari World Bank GEM Commodities API.
        Uses source=6 (Global Economic Monitor Commodities) for commodity price data.
        """
        # Primary: GEM Commodities source
        url = f"https://api.worldbank.org/v2/country/WLD/indicator/{wb_code}"
        params = {
            "format": "json",
            "per_page": "500",
            "date": f"{self.year_start}:{self.year_end}",
            "source": "6",  # GEM Commodities database
        }

        resp = await self.client.get(url, params=params)

        # Fallback: try without source filter if source=6 fails
        if resp.status_code != 200:
            logger.debug(f"[{self.name}] Source 6 failed for {wb_code}, trying without source filter")
            params.pop("source")
            resp = await self.client.get(url, params=params)

        if resp.status_code != 200:
            logger.warning(f"[{self.name}] WB API HTTP {resp.status_code} for {wb_code}")
            return []

        try:
            payload = resp.json()
        except Exception:
            return []

        if not payload or len(payload) < 2 or not payload[1]:
            return []

        records = payload[1]
        results = []
        for rec in records:
            val = rec.get("value")
            if val is None:
                continue
            date_str = str(rec.get("date", ""))
            # World Bank monthly format: "2024M01" or annual "2024"
            if "M" in date_str:
                parts = date_str.split("M")
                if len(parts) == 2:
                    periode = f"{parts[0]}-{parts[1].zfill(2)}-01"
                else:
                    continue
            elif len(date_str) == 4:
                periode = f"{date_str}-01-01"
            else:
                continue

            results.append({
                "periode": date.fromisoformat(periode),
                "commodity": commodity,
                "price": float(val),
                "unit": unit,
                "sumber": "WORLD_BANK",
            })

        return results

    async def _load(self, data: list[dict]) -> int:
        count = 0
        prev_prices: dict[str, float] = {}

        # Sort by date to compute change_pct
        data.sort(key=lambda x: x["periode"])

        for row in data:
            commodity = row["commodity"]
            price = row["price"]

            change_pct = None
            if commodity in prev_prices and prev_prices[commodity] > 0:
                change_pct = round((price - prev_prices[commodity]) / prev_prices[commodity] * 100, 4)
            prev_prices[commodity] = price

            await self.db.execute(
                text("""
                    INSERT INTO ext_commodity_price (periode, commodity, price, unit, change_pct, sumber)
                    VALUES (:periode, :commodity, :price, :unit, :change_pct, :sumber)
                    ON CONFLICT (periode, commodity)
                    DO UPDATE SET price = EXCLUDED.price, change_pct = EXCLUDED.change_pct
                """),
                {**row, "change_pct": change_pct},
            )
            count += 1

        await self.db.commit()
        return count
