"""
Supply-Demand Balance & Redistribution Service.

Menentukan wilayah surplus/defisit per komoditas dan
menghasilkan rekomendasi redistribusi pangan.
"""

import logging
import math
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SupplyDemandService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_balance(self, tanggal: date | None = None) -> list[dict]:
        """Analyze supply-demand balance per commodity-region."""
        tanggal = tanggal or date.today()

        query = text("""
            WITH current_prices AS (
                SELECT
                    fpd.commodity_id, fpd.region_id, fpd.harga,
                    dc.nama_display AS commodity_name,
                    dr.nama_provinsi, dr.kode_wilayah,
                    dr.latitude, dr.longitude
                FROM fact_price_daily fpd
                JOIN dim_commodity dc ON dc.id = fpd.commodity_id
                JOIN dim_region dr ON dr.id = fpd.region_id
                WHERE fpd.tanggal = :tanggal
                  AND dr.level_wilayah = 'provinsi'
            ),
            median_prices AS (
                SELECT
                    commodity_id,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY harga) AS median_harga,
                    AVG(harga) AS avg_harga
                FROM current_prices
                GROUP BY commodity_id
            ),
            stock_status AS (
                SELECT commodity_id, region_id, status, stok
                FROM fact_supply_stock
                WHERE tanggal = (
                    SELECT MAX(tanggal) FROM fact_supply_stock WHERE tanggal <= :tanggal
                )
            )
            SELECT
                cp.commodity_id, cp.region_id,
                cp.commodity_name, cp.nama_provinsi, cp.kode_wilayah,
                cp.latitude, cp.longitude,
                cp.harga,
                mp.median_harga,
                ROUND(((cp.harga - mp.median_harga) / NULLIF(mp.median_harga, 0) * 100)::numeric, 2) AS price_deviation,
                COALESCE(ss.status, 'unknown') AS stock_status,
                COALESCE(ss.stok, 0) AS stok_level
            FROM current_prices cp
            JOIN median_prices mp ON mp.commodity_id = cp.commodity_id
            LEFT JOIN stock_status ss ON ss.commodity_id = cp.commodity_id AND ss.region_id = cp.region_id
            ORDER BY cp.commodity_id, price_deviation
        """)

        result = await self.db.execute(query, {"tanggal": tanggal})
        rows = result.fetchall()

        balances = []
        for row in rows:
            deviation = float(row.price_deviation) if row.price_deviation else 0
            stock = row.stock_status

            # Classify: surplus / balanced / deficit
            if deviation < -10 or stock == "aman":
                status = "surplus"
            elif deviation > 15 or stock == "kritis":
                status = "deficit"
            elif deviation > 5 or stock == "waspada":
                status = "waspada"
            else:
                status = "balanced"

            balances.append({
                "commodity_id": row.commodity_id,
                "region_id": row.region_id,
                "commodity": row.commodity_name,
                "provinsi": row.nama_provinsi,
                "kode_wilayah": row.kode_wilayah,
                "latitude": float(row.latitude) if row.latitude else None,
                "longitude": float(row.longitude) if row.longitude else None,
                "harga": float(row.harga),
                "median_harga": float(row.median_harga) if row.median_harga else 0,
                "price_deviation": deviation,
                "stock_status": stock,
                "stok_level": float(row.stok_level) if row.stok_level else 0,
                "balance_status": status,
            })

        return balances

    async def get_recommendations(self, tanggal: date | None = None) -> list[dict]:
        """Generate redistribution recommendations."""
        tanggal = tanggal or date.today()
        balances = await self.analyze_balance(tanggal)

        # Group by commodity
        by_commodity: dict[int, list[dict]] = {}
        for b in balances:
            by_commodity.setdefault(b["commodity_id"], []).append(b)

        recommendations = []
        for commodity_id, regions in by_commodity.items():
            surplus = [r for r in regions if r["balance_status"] == "surplus"]
            deficit = [r for r in regions if r["balance_status"] in ("deficit", "waspada")]

            if not surplus or not deficit:
                continue

            # For each deficit region, find nearest surplus region
            for def_region in deficit:
                if not def_region["latitude"] or not def_region["longitude"]:
                    continue

                best_source = None
                best_distance = float("inf")

                for sur_region in surplus:
                    if not sur_region["latitude"] or not sur_region["longitude"]:
                        continue

                    dist = self._haversine(
                        def_region["latitude"], def_region["longitude"],
                        sur_region["latitude"], sur_region["longitude"],
                    )
                    if dist < best_distance:
                        best_distance = dist
                        best_source = sur_region

                if best_source and best_distance < 3000:  # max 3000 km
                    price_gap = def_region["harga"] - best_source["harga"]
                    # Estimate tonnage based on price gap magnitude
                    est_tonnage = max(5, min(100, round(abs(def_region["price_deviation"]) * 2)))

                    recommendations.append({
                        "commodity": def_region["commodity"],
                        "commodity_id": commodity_id,
                        "from_region": best_source["provinsi"],
                        "from_kode": best_source["kode_wilayah"],
                        "from_harga": best_source["harga"],
                        "to_region": def_region["provinsi"],
                        "to_kode": def_region["kode_wilayah"],
                        "to_harga": def_region["harga"],
                        "price_gap": round(price_gap, 0),
                        "distance_km": round(best_distance, 0),
                        "estimated_tonnage": est_tonnage,
                        "urgency": "tinggi" if def_region["balance_status"] == "deficit" else "sedang",
                    })

        # Sort by urgency then price gap
        recommendations.sort(
            key=lambda r: (0 if r["urgency"] == "tinggi" else 1, -r["price_gap"])
        )

        return recommendations

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km between two points using Haversine formula."""
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
