"""
Pipeline: Global Energy Prices (Brent Crude, etc.)

Sumber:
  1. US EIA API v2 (https://api.eia.gov) — memerlukan API key gratis
     Daftar di https://www.eia.gov/opendata/register.php
  2. Fallback: World Bank monthly Brent data (tanpa key)
Frekuensi: Harian
"""

import logging
import os
from datetime import date, timedelta

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EnergyPricePipeline:
    """Pipeline untuk harga energi global (Brent crude dll)."""

    name = "energy_price"

    def __init__(self, db: AsyncSession, days: int = 90):
        self.db = db
        self.days = days
        self.eia_api_key = os.getenv("EIA_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def run(self) -> int:
        logger.info(f"[{self.name}] Fetching last {self.days} days of energy prices")

        try:
            data = await self._fetch()
            if not data:
                return 0
            count = await self._load(data)
            logger.info(f"[{self.name}] Loaded {count} records")
            return count
        finally:
            await self.client.aclose()

    async def _fetch(self) -> list[dict]:
        """
        Fetch Brent crude prices.
        Primary: EIA API v2 (requires free API key).
        Fallback: World Bank monthly data (no key needed).
        """
        results = []

        # Try EIA first (daily data, most granular)
        if self.eia_api_key:
            try:
                brent = await self._fetch_brent_from_eia()
                results.extend(brent)
            except Exception as e:
                logger.warning(f"[{self.name}] EIA fetch failed: {e}")
        else:
            logger.info(f"[{self.name}] EIA_API_KEY not set, skipping EIA")

        if not results:
            # Fallback: World Bank monthly Brent data (no key required)
            try:
                brent_wb = await self._fetch_brent_from_worldbank()
                results.extend(brent_wb)
            except Exception as e:
                logger.warning(f"[{self.name}] World Bank fallback failed: {e}")

        return results

    async def _fetch_brent_from_eia(self) -> list[dict]:
        """
        Fetch Brent crude from EIA open data API v2.
        Series: PET.RBRTE.D (Europe Brent Spot Price FOB, Daily)
        Requires API key (free registration at https://www.eia.gov/opendata/register.php)
        """
        end = date.today()
        start = end - timedelta(days=self.days)

        url = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        params = {
            "api_key": self.eia_api_key,
            "frequency": "daily",
            "data[0]": "value",
            "facets[product][]": "EPCBRENT",
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "length": "5000",
        }

        resp = await self.client.get(url, params=params)
        if resp.status_code != 200:
            logger.warning(f"[{self.name}] EIA HTTP {resp.status_code}")
            return []

        payload = resp.json()

        # Check for API errors
        if "error" in payload:
            logger.warning(f"[{self.name}] EIA API error: {payload['error']}")
            return []

        data_rows = payload.get("response", {}).get("data", [])

        results = []
        prev_price = None
        for row in data_rows:
            period = row.get("period")
            value = row.get("value")
            if not period or value is None:
                continue
            try:
                price = float(value)
            except (ValueError, TypeError):
                continue

            change_pct = None
            if prev_price and prev_price > 0:
                change_pct = round((price - prev_price) / prev_price * 100, 4)
            prev_price = price

            results.append({
                "tanggal": date.fromisoformat(period),
                "commodity": "brent",
                "price": price,
                "change_pct": change_pct,
                "sumber": "EIA",
            })

        return results

    async def _fetch_brent_from_worldbank(self) -> list[dict]:
        """
        Fallback: fetch Brent crude from World Bank GEM Commodities (monthly).
        Source 6 = Global Economic Monitor Commodities.
        """
        url = "https://api.worldbank.org/v2/country/WLD/indicator/CRUDE_BRENT"
        params = {
            "format": "json",
            "per_page": "120",
            "date": f"2023:{date.today().year}",
            "source": "6",
        }

        resp = await self.client.get(url, params=params)
        if resp.status_code != 200:
            return []

        try:
            payload = resp.json()
        except Exception:
            return []

        if not payload or len(payload) < 2 or not payload[1]:
            return []

        results = []
        prev_price = None
        for rec in sorted(payload[1], key=lambda x: str(x.get("date", ""))):
            val = rec.get("value")
            if val is None:
                continue
            date_str = str(rec.get("date", ""))

            if "M" in date_str:
                parts = date_str.split("M")
                if len(parts) == 2:
                    tanggal = f"{parts[0]}-{parts[1].zfill(2)}-01"
                else:
                    continue
            elif len(date_str) == 4:
                tanggal = f"{date_str}-01-01"
            else:
                continue

            price = float(val)
            change_pct = None
            if prev_price and prev_price > 0:
                change_pct = round((price - prev_price) / prev_price * 100, 4)
            prev_price = price

            results.append({
                "tanggal": date.fromisoformat(tanggal),
                "commodity": "brent",
                "price": price,
                "change_pct": change_pct,
                "sumber": "WORLD_BANK",
            })

        return results

    async def _load(self, data: list[dict]) -> int:
        count = 0
        for row in data:
            await self.db.execute(
                text("""
                    INSERT INTO ext_energy_price (tanggal, commodity, price, change_pct, sumber)
                    VALUES (:tanggal, :commodity, :price, :change_pct, :sumber)
                    ON CONFLICT (tanggal, commodity)
                    DO UPDATE SET price = EXCLUDED.price, change_pct = EXCLUDED.change_pct
                """),
                row,
            )
            count += 1
        await self.db.commit()
        return count
