from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class RankingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_commodity_ranking(self, sort: str = "weekly_change", limit: int = 8) -> list[dict]:
        """Ranking komoditas berdasarkan perubahan harga (rata-rata nasional)."""
        order_col = {
            "weekly_change": "avg_mingguan",
            "daily_change": "avg_harian",
            "volatility": "avg_vol",
        }.get(sort, "avg_mingguan")

        query = text(f"""
            WITH latest AS (
                SELECT MAX(tanggal) AS max_date FROM fact_price_daily
            ),
            national_avg AS (
                SELECT
                    fpd.commodity_id,
                    AVG(fpd.harga) AS avg_harga,
                    AVG(fpd.perubahan_harian) AS avg_harian,
                    AVG(fpd.perubahan_mingguan) AS avg_mingguan,
                    AVG(fpd.perubahan_bulanan) AS avg_bulanan
                FROM fact_price_daily fpd, latest l
                WHERE fpd.tanggal = l.max_date
                GROUP BY fpd.commodity_id
            ),
            vol AS (
                SELECT
                    commodity_id,
                    STDDEV(harga) / NULLIF(AVG(harga), 0) * 100 AS avg_vol
                FROM fact_price_daily
                WHERE tanggal >= (SELECT max_date - 14 FROM latest)
                GROUP BY commodity_id
            )
            SELECT
                dc.kode_komoditas,
                dc.nama_display,
                dc.kategori,
                dc.satuan,
                ROUND(na.avg_harga::numeric, 0) AS harga_terakhir,
                ROUND(COALESCE(na.avg_harian, 0)::numeric, 2) AS perubahan_harian,
                ROUND(COALESCE(na.avg_mingguan, 0)::numeric, 2) AS perubahan_mingguan,
                ROUND(COALESCE(na.avg_bulanan, 0)::numeric, 2) AS perubahan_bulanan,
                ROUND(COALESCE(v.avg_vol, 0)::numeric, 2) AS volatilitas
            FROM national_avg na
            JOIN dim_commodity dc ON dc.id = na.commodity_id
            LEFT JOIN vol v ON v.commodity_id = na.commodity_id
            ORDER BY {order_col} DESC NULLS LAST
            LIMIT :limit
        """)

        result = await self.db.execute(query, {"limit": limit})
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_region_ranking(self, sort: str = "pressure", limit: int = 10) -> list[dict]:
        """Ranking wilayah berdasarkan tekanan harga."""
        query = text("""
            WITH latest AS (
                SELECT MAX(tanggal) AS max_date FROM fact_price_daily
            ),
            region_pressure AS (
                SELECT
                    fpd.region_id,
                    AVG(fpd.perubahan_mingguan) AS avg_change,
                    COUNT(CASE WHEN fpd.perubahan_mingguan > 5 THEN 1 END) AS rising_count
                FROM fact_price_daily fpd, latest l
                WHERE fpd.tanggal = l.max_date
                GROUP BY fpd.region_id
            )
            SELECT
                dr.kode_wilayah,
                dr.nama_provinsi,
                dr.level_wilayah,
                ROUND(COALESCE(rp.avg_change, 0)::numeric, 2) AS avg_price_change,
                rp.rising_count,
                COALESCE(
                    (SELECT COUNT(*) FROM analytics_alerts aa
                     WHERE aa.region_id = dr.id AND aa.is_active = TRUE),
                    0
                ) AS alert_count,
                COALESCE(
                    (SELECT ROUND(AVG(risk_score_total)::numeric, 1)
                     FROM analytics_risk_score ars, latest l
                     WHERE ars.region_id = dr.id AND ars.tanggal = l.max_date),
                    0
                ) AS avg_risk_score
            FROM dim_region dr
            LEFT JOIN region_pressure rp ON rp.region_id = dr.id
            WHERE dr.level_wilayah = 'provinsi'
            ORDER BY avg_change DESC NULLS LAST
            LIMIT :limit
        """)

        result = await self.db.execute(query, {"limit": limit})
        return [dict(row._mapping) for row in result.fetchall()]
