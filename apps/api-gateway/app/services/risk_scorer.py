from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# Risk score weights (match src/lib/constants.ts)
WEIGHTS = {
    "kenaikan_7d": 0.25,
    "kenaikan_30d": 0.20,
    "volatilitas": 0.20,
    "deviasi_wilayah": 0.15,
    "sinyal_cuaca": 0.10,
    "sinyal_stok": 0.10,
}


class RiskScorer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_all_scores(self, tanggal: date) -> None:
        """Hitung risk score untuk semua pasangan komoditas-wilayah."""
        query = text("""
            WITH price_changes AS (
                SELECT
                    fpd.commodity_id,
                    fpd.region_id,
                    fpd.harga AS harga_now,
                    prev7.harga AS harga_7d,
                    prev30.harga AS harga_30d
                FROM fact_price_daily fpd
                LEFT JOIN fact_price_daily prev7
                    ON prev7.commodity_id = fpd.commodity_id
                    AND prev7.region_id = fpd.region_id
                    AND prev7.tanggal = :week_ago
                LEFT JOIN fact_price_daily prev30
                    ON prev30.commodity_id = fpd.commodity_id
                    AND prev30.region_id = fpd.region_id
                    AND prev30.tanggal = :month_ago
                WHERE fpd.tanggal = :tanggal
            ),
            volatility AS (
                SELECT
                    commodity_id, region_id,
                    STDDEV(harga) / NULLIF(AVG(harga), 0) * 100 AS cv
                FROM fact_price_daily
                WHERE tanggal BETWEEN :vol_start AND :tanggal
                GROUP BY commodity_id, region_id
            ),
            median_prices AS (
                SELECT
                    commodity_id,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY harga) AS median_harga
                FROM fact_price_daily
                WHERE tanggal = :tanggal
                GROUP BY commodity_id
            ),
            weather AS (
                SELECT
                    region_id,
                    CASE warning_level
                        WHEN 'normal' THEN 0
                        WHEN 'waspada' THEN 33
                        WHEN 'siaga' THEN 66
                        WHEN 'awas' THEN 100
                        ELSE 0
                    END AS weather_score
                FROM fact_climate
                WHERE tanggal = :tanggal
            ),
            stock AS (
                SELECT
                    region_id, commodity_id,
                    CASE status
                        WHEN 'aman' THEN 0
                        WHEN 'waspada' THEN 50
                        WHEN 'kritis' THEN 100
                        ELSE 0
                    END AS stock_score
                FROM fact_supply_stock
                WHERE tanggal = :tanggal
            )
            SELECT
                pc.commodity_id,
                pc.region_id,
                -- Skor kenaikan 7 hari (normalize 0-20% ke 0-100)
                LEAST(100, GREATEST(0,
                    CASE WHEN pc.harga_7d > 0
                        THEN ((pc.harga_now - pc.harga_7d) / pc.harga_7d * 100) / 20 * 100
                        ELSE 0
                    END
                )) AS skor_7d,
                -- Skor kenaikan 30 hari (normalize 0-30% ke 0-100)
                LEAST(100, GREATEST(0,
                    CASE WHEN pc.harga_30d > 0
                        THEN ((pc.harga_now - pc.harga_30d) / pc.harga_30d * 100) / 30 * 100
                        ELSE 0
                    END
                )) AS skor_30d,
                -- Skor volatilitas (normalize 0-25% ke 0-100)
                LEAST(100, GREATEST(0, COALESCE(v.cv / 25 * 100, 0))) AS skor_vol,
                -- Skor deviasi wilayah (normalize 0-30% ke 0-100)
                LEAST(100, GREATEST(0,
                    CASE WHEN mp.median_harga > 0
                        THEN ABS((pc.harga_now - mp.median_harga) / mp.median_harga * 100) / 30 * 100
                        ELSE 0
                    END
                )) AS skor_dev,
                -- Skor cuaca
                COALESCE(w.weather_score, 0) AS skor_cuaca,
                -- Skor stok
                COALESCE(s.stock_score, 0) AS skor_stok
            FROM price_changes pc
            LEFT JOIN volatility v ON v.commodity_id = pc.commodity_id AND v.region_id = pc.region_id
            LEFT JOIN median_prices mp ON mp.commodity_id = pc.commodity_id
            LEFT JOIN weather w ON w.region_id = pc.region_id
            LEFT JOIN stock s ON s.commodity_id = pc.commodity_id AND s.region_id = pc.region_id
        """)

        result = await self.db.execute(
            query,
            {
                "tanggal": tanggal,
                "week_ago": tanggal - timedelta(days=7),
                "month_ago": tanggal - timedelta(days=30),
                "vol_start": tanggal - timedelta(days=14),
            },
        )

        for row in result.fetchall():
            total = (
                float(row.skor_7d) * WEIGHTS["kenaikan_7d"]
                + float(row.skor_30d) * WEIGHTS["kenaikan_30d"]
                + float(row.skor_vol) * WEIGHTS["volatilitas"]
                + float(row.skor_dev) * WEIGHTS["deviasi_wilayah"]
                + float(row.skor_cuaca) * WEIGHTS["sinyal_cuaca"]
                + float(row.skor_stok) * WEIGHTS["sinyal_stok"]
            )

            category = "rendah" if total < 33 else "sedang" if total < 66 else "tinggi"

            await self.db.execute(
                text("""
                    INSERT INTO analytics_risk_score
                        (tanggal, region_id, commodity_id,
                         skor_kenaikan_7d, skor_kenaikan_30d, skor_volatilitas,
                         skor_deviasi_wilayah, skor_cuaca, skor_stok,
                         risk_score_total, risk_category)
                    VALUES
                        (:tanggal, :region_id, :commodity_id,
                         :skor_7d, :skor_30d, :skor_vol,
                         :skor_dev, :skor_cuaca, :skor_stok,
                         :total, :category)
                    ON CONFLICT (tanggal, region_id, commodity_id)
                    DO UPDATE SET
                        skor_kenaikan_7d = EXCLUDED.skor_kenaikan_7d,
                        skor_kenaikan_30d = EXCLUDED.skor_kenaikan_30d,
                        skor_volatilitas = EXCLUDED.skor_volatilitas,
                        skor_deviasi_wilayah = EXCLUDED.skor_deviasi_wilayah,
                        skor_cuaca = EXCLUDED.skor_cuaca,
                        skor_stok = EXCLUDED.skor_stok,
                        risk_score_total = EXCLUDED.risk_score_total,
                        risk_category = EXCLUDED.risk_category
                """),
                {
                    "tanggal": tanggal,
                    "region_id": row.region_id,
                    "commodity_id": row.commodity_id,
                    "skor_7d": round(float(row.skor_7d), 2),
                    "skor_30d": round(float(row.skor_30d), 2),
                    "skor_vol": round(float(row.skor_vol), 2),
                    "skor_dev": round(float(row.skor_dev), 2),
                    "skor_cuaca": round(float(row.skor_cuaca), 2),
                    "skor_stok": round(float(row.skor_stok), 2),
                    "total": round(total, 2),
                    "category": category,
                },
            )

        await self.db.commit()

    async def get_all_scores(self, tanggal: date) -> list[dict]:
        """Get semua risk scores untuk tanggal tertentu."""
        query = text("""
            SELECT
                ars.*,
                dr.nama_provinsi, dr.kode_wilayah,
                dc.nama_display, dc.kode_komoditas
            FROM analytics_risk_score ars
            JOIN dim_region dr ON dr.id = ars.region_id
            JOIN dim_commodity dc ON dc.id = ars.commodity_id
            WHERE ars.tanggal = :tanggal
            ORDER BY ars.risk_score_total DESC
        """)

        result = await self.db.execute(query, {"tanggal": tanggal})
        return [dict(row._mapping) for row in result.fetchall()]
