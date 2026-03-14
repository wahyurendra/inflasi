"""
Pipeline: Exchange Rate USD/IDR

Sumber primer: European Central Bank (ECB) via Frankfurter API (gratis, no key)
Sumber alternatif: exchangerate.host
Frekuensi: Harian
"""

import logging
from datetime import date, timedelta

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ExchangeRatePipeline:
    """Pipeline untuk kurs USD/IDR harian."""

    name = "exchange_rate"

    def __init__(self, db: AsyncSession, start_date: date | None = None, end_date: date | None = None):
        self.db = db
        self.end_date = end_date or date.today()
        self.start_date = start_date or (self.end_date - timedelta(days=30))
        self.client = httpx.AsyncClient(timeout=30.0)

    async def run(self) -> int:
        logger.info(f"[{self.name}] Fetching {self.start_date} to {self.end_date}")

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
        """Fetch from Frankfurter API (ECB data, free, no key)."""
        url = f"https://api.frankfurter.app/{self.start_date}..{self.end_date}"
        params = {"from": "USD", "to": "IDR"}

        resp = await self.client.get(url, params=params)
        if resp.status_code != 200:
            logger.error(f"[{self.name}] API error: {resp.status_code}")
            return []

        payload = resp.json()
        rates = payload.get("rates", {})

        results = []
        sorted_dates = sorted(rates.keys())
        prev_rate = None
        for d in sorted_dates:
            rate = rates[d].get("IDR")
            if rate is None:
                continue
            change_pct = None
            if prev_rate and prev_rate > 0:
                change_pct = round((rate - prev_rate) / prev_rate * 100, 4)
            results.append({
                "tanggal": date.fromisoformat(d),
                "kurs_tengah": rate,
                "change_pct": change_pct,
            })
            prev_rate = rate

        return results

    async def _load(self, data: list[dict]) -> int:
        count = 0
        for row in data:
            await self.db.execute(
                text("""
                    INSERT INTO ext_exchange_rate (tanggal, kurs_tengah, change_pct, sumber)
                    VALUES (:tanggal, :kurs_tengah, :change_pct, 'ECB')
                    ON CONFLICT (tanggal)
                    DO UPDATE SET kurs_tengah = EXCLUDED.kurs_tengah,
                                  change_pct = EXCLUDED.change_pct
                """),
                row,
            )
            count += 1
        await self.db.commit()
        return count
