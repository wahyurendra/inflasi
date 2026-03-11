from datetime import date, timedelta

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PriceCalculator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_price_changes(
        self, commodity_code: str, region_code: str, tanggal: date
    ) -> dict:
        """Hitung perubahan harga harian, mingguan, bulanan."""
        query = text("""
            SELECT fpd.tanggal, fpd.harga
            FROM fact_price_daily fpd
            JOIN dim_commodity dc ON dc.id = fpd.commodity_id
            JOIN dim_region dr ON dr.id = fpd.region_id
            WHERE dc.kode_komoditas = :commodity_code
              AND dr.kode_wilayah = :region_code
              AND fpd.tanggal BETWEEN :start_date AND :end_date
            ORDER BY fpd.tanggal DESC
        """)

        result = await self.db.execute(
            query,
            {
                "commodity_code": commodity_code,
                "region_code": region_code,
                "start_date": tanggal - timedelta(days=35),
                "end_date": tanggal,
            },
        )
        rows = result.fetchall()

        if not rows:
            return {"harga": None, "harian": None, "mingguan": None, "bulanan": None}

        harga_hari_ini = float(rows[0].harga)
        harga_kemarin = float(rows[1].harga) if len(rows) > 1 else None
        harga_7d = self._find_price_at_offset(rows, tanggal, 7)
        harga_30d = self._find_price_at_offset(rows, tanggal, 30)

        return {
            "tanggal": tanggal.isoformat(),
            "harga": harga_hari_ini,
            "harian": self._pct_change(harga_hari_ini, harga_kemarin),
            "mingguan": self._pct_change(harga_hari_ini, harga_7d),
            "bulanan": self._pct_change(harga_hari_ini, harga_30d),
        }

    async def get_volatility(
        self, commodity_code: str, region_code: str, window: int = 14
    ) -> dict:
        """Hitung Coefficient of Variation (CV) sebagai ukuran volatilitas."""
        query = text("""
            SELECT fpd.harga
            FROM fact_price_daily fpd
            JOIN dim_commodity dc ON dc.id = fpd.commodity_id
            JOIN dim_region dr ON dr.id = fpd.region_id
            WHERE dc.kode_komoditas = :commodity_code
              AND dr.kode_wilayah = :region_code
            ORDER BY fpd.tanggal DESC
            LIMIT :window
        """)

        result = await self.db.execute(
            query,
            {"commodity_code": commodity_code, "region_code": region_code, "window": window},
        )
        prices = [float(row.harga) for row in result.fetchall()]

        if len(prices) < 2:
            return {"cv": None, "std": None, "mean": None}

        arr = np.array(prices)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))
        cv = (std_val / mean_val * 100) if mean_val > 0 else 0

        return {
            "cv": round(cv, 2),
            "std": round(std_val, 2),
            "mean": round(mean_val, 2),
            "window": window,
            "data_points": len(prices),
        }

    async def calculate_all_changes(self, tanggal: date) -> None:
        """Hitung dan update perubahan harga untuk semua komoditas-wilayah pada tanggal tertentu."""
        query = text("""
            UPDATE fact_price_daily fpd
            SET
                harga_kemarin = prev.harga,
                perubahan_harian = CASE
                    WHEN prev.harga > 0 THEN ROUND(((fpd.harga - prev.harga) / prev.harga * 100)::numeric, 4)
                    ELSE NULL
                END,
                perubahan_mingguan = CASE
                    WHEN w7.harga > 0 THEN ROUND(((fpd.harga - w7.harga) / w7.harga * 100)::numeric, 4)
                    ELSE NULL
                END,
                perubahan_bulanan = CASE
                    WHEN m30.harga > 0 THEN ROUND(((fpd.harga - m30.harga) / m30.harga * 100)::numeric, 4)
                    ELSE NULL
                END
            FROM (
                SELECT commodity_id, region_id, harga
                FROM fact_price_daily
                WHERE tanggal = :yesterday
            ) prev,
            (
                SELECT commodity_id, region_id, harga
                FROM fact_price_daily
                WHERE tanggal = :week_ago
            ) w7,
            (
                SELECT commodity_id, region_id, harga
                FROM fact_price_daily
                WHERE tanggal = :month_ago
            ) m30
            WHERE fpd.tanggal = :tanggal
              AND fpd.commodity_id = prev.commodity_id AND fpd.region_id = prev.region_id
              AND fpd.commodity_id = w7.commodity_id AND fpd.region_id = w7.region_id
              AND fpd.commodity_id = m30.commodity_id AND fpd.region_id = m30.region_id
        """)

        await self.db.execute(
            query,
            {
                "tanggal": tanggal,
                "yesterday": tanggal - timedelta(days=1),
                "week_ago": tanggal - timedelta(days=7),
                "month_ago": tanggal - timedelta(days=30),
            },
        )
        await self.db.commit()

    def _find_price_at_offset(self, rows, tanggal: date, days: int) -> float | None:
        target = tanggal - timedelta(days=days)
        for row in rows:
            if row.tanggal <= target:
                return float(row.harga)
        return None

    @staticmethod
    def _pct_change(current: float, previous: float | None) -> float | None:
        if previous is None or previous == 0:
            return None
        return round((current - previous) / previous * 100, 4)
