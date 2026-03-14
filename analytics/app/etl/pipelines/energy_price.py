"""
Pipeline: Global Energy Prices (Brent Crude, etc.)

Sumber: US EIA API (free, key optional for basic), alternative APIs
Frekuensi: Harian
"""

import logging
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
        Fetch Brent crude prices from free API.
        Uses EIA (Energy Information Administration) open data or alternative.
        """
        results = []

        # Try free commodity API endpoints
        try:
            brent = await self._fetch_brent_from_eia()
            results.extend(brent)
        except Exception as e:
            logger.warning(f"[{self.name}] EIA fetch failed: {e}")

        if not results:
            # Fallback: World Bank monthly Brent data
            try:
                brent_wb = await self._fetch_brent_from_worldbank()
                results.extend(brent_wb)
            except Exception as e:
                logger.warning(f"[{self.name}] World Bank fallback failed: {e}")

        return results

    async def _fetch_brent_from_eia(self) -> list[dict]:
        """
        Fetch Brent crude from EIA open data API.
        Series: PET.RBRTE.D (Europe Brent Spot Price FOB, Daily)
        """
        end = date.today()
        start = end - timedelta(days=self.days)

        # EIA API v2 (free, no key for basic access)
        url = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        params = {
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
            return []

        payload = resp.json()
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
        """Fallback: fetch from World Bank (monthly)."""
        url = "https://api.worldbank.org/v2/country/WLD/indicator/CRUDE_BRENT"
        params = {
            "format": "json",
            "per_page": "60",
            "date": f"2023:{date.today().year}",
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
        for rec in sorted(payload[1], key=lambda x: str(x.get("date", ""))):
            val = rec.get("value")
            if val is None:
                continue
            date_str = str(rec.get("date", ""))
            if "M" in date_str:
                parts = date_str.split("M")
                tanggal = f"{parts[0]}-{parts[1].zfill(2)}-01"
            elif len(date_str) == 4:
                tanggal = f"{date_str}-01-01"
            else:
                continue

            results.append({
                "tanggal": date.fromisoformat(tanggal),
                "commodity": "brent",
                "price": float(val),
                "change_pct": None,
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
