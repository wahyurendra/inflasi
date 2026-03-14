"""
Pipeline: GDELT News Intelligence

Sumber: GDELT Project (Global Database of Events, Language, and Tone)
API: https://api.gdeltproject.org/api/v2/doc/doc
Frekuensi: Harian
Data: Berita global terkait pangan, energi, geopolitik, iklim

Kategori yang dimonitor:
  - food_supply: harga pangan, kelangkaan, food security
  - energy: minyak, gas, BBM, energi
  - geopolitics: konflik, perang, sanksi, embargo
  - climate: banjir, kekeringan, El Nino, La Nina
  - agriculture: pertanian, panen, produksi, pupuk
  - indonesia: berita domestik terkait ekonomi/pangan
"""

import logging
from datetime import date, timedelta

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# GDELT search queries per kategori
GDELT_QUERIES: dict[str, str] = {
    "food_supply": '("food price" OR "food inflation" OR "food crisis" OR "food shortage" OR "rice price" OR "wheat price" OR "palm oil price")',
    "energy": '("oil price" OR "crude oil" OR "brent" OR "energy price" OR "fuel price" OR "diesel" OR "LNG price")',
    "geopolitics": '("trade war" OR "sanctions" OR "embargo" OR "shipping disruption" OR "strait of hormuz" OR "red sea" OR "suez canal")',
    "climate": '("flood" OR "drought" OR "El Nino" OR "La Nina" OR "extreme weather" OR "crop failure" OR "harvest" OR "monsoon")',
    "agriculture": '("fertilizer price" OR "urea price" OR "crop production" OR "agricultural" OR "farming" OR "harvest failure")',
    "indonesia": '("Indonesia" AND ("inflation" OR "food price" OR "rice" OR "economy" OR "rupiah" OR "Bank Indonesia"))',
}


class GDELTNewsPipeline:
    """Pipeline untuk news intelligence dari GDELT."""

    name = "gdelt_news"

    def __init__(self, db: AsyncSession, days: int = 3):
        self.db = db
        self.days = days
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; InflasiBot/1.0)"},
        )

    async def run(self) -> int:
        logger.info(f"[{self.name}] Fetching news signals for last {self.days} days")
        total = 0

        try:
            import asyncio
            for kategori, query in GDELT_QUERIES.items():
                try:
                    articles = await self._fetch_category(kategori, query)
                    if articles:
                        count = await self._load(articles)
                        total += count
                        logger.debug(f"[{self.name}] {kategori}: {count} articles")
                except Exception as e:
                    logger.warning(f"[{self.name}] Failed {kategori}: {e}")
                # Rate limit: GDELT allows ~1 req/sec
                await asyncio.sleep(1.5)

            logger.info(f"[{self.name}] Total loaded: {total} articles")
            return total
        finally:
            await self.client.aclose()

    async def _fetch_category(self, kategori: str, query: str) -> list[dict]:
        """
        Fetch berita dari GDELT DOC API v2.
        Returns top articles sorted by relevance.
        """
        end = date.today()
        start = end - timedelta(days=self.days)

        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": query,
            "mode": "ArtList",
            "maxrecords": "15",
            "timespan": f"{self.days}d",
            "format": "json",
            "sort": "DateDesc",
        }

        resp = await self.client.get(url, params=params)
        if resp.status_code != 200:
            logger.warning(f"[{self.name}] GDELT API {resp.status_code} for {kategori}")
            return []

        try:
            payload = resp.json()
        except Exception:
            # GDELT sometimes returns HTML errors
            logger.warning(f"[{self.name}] Non-JSON response for {kategori}")
            return []

        articles = payload.get("articles", [])
        results = []

        for art in articles:
            title = art.get("title", "").strip()
            url_link = art.get("url", "")
            source = art.get("domain", art.get("source", ""))
            seendate = art.get("seendate", "")
            tone = art.get("tone", 0)

            if not title:
                continue

            # Parse date from seendate (format: YYYYMMDDTHHmmssZ)
            try:
                tanggal = date(int(seendate[:4]), int(seendate[4:6]), int(seendate[6:8]))
            except (IndexError, TypeError, ValueError):
                tanggal = end

            # Map GDELT tone to sentimen
            try:
                tone_val = float(tone) if tone else 0
            except (ValueError, TypeError):
                tone_val = 0

            if tone_val < -3:
                sentimen = "negative"
            elif tone_val > 3:
                sentimen = "positive"
            else:
                sentimen = "neutral"

            # Compute relevance score (0-100)
            # Based on: source reliability + keyword density
            relevansi = min(100, max(10, 50 + abs(tone_val) * 5))

            results.append({
                "tanggal": tanggal,
                "kategori": kategori,
                "judul": title[:500],
                "sumber": source[:100],
                "url": url_link[:500] if url_link else None,
                "sentimen": sentimen,
                "relevansi": relevansi,
                "ringkasan": None,  # Could add AI summarization later
            })

        return results

    async def _load(self, data: list[dict]) -> int:
        """Insert news signals (no upsert, allow multiple per day/category)."""
        count = 0
        for row in data:
            # Check duplicate by title+date
            existing = await self.db.execute(
                text("""
                    SELECT id FROM ext_news_signal
                    WHERE tanggal = :tanggal AND judul = :judul
                    LIMIT 1
                """),
                {"tanggal": row["tanggal"], "judul": row["judul"]},
            )
            if existing.fetchone():
                continue

            await self.db.execute(
                text("""
                    INSERT INTO ext_news_signal (tanggal, kategori, judul, sumber, url, sentimen, relevansi, ringkasan)
                    VALUES (:tanggal, :kategori, :judul, :sumber, :url, :sentimen, :relevansi, :ringkasan)
                """),
                row,
            )
            count += 1

        await self.db.commit()
        return count
