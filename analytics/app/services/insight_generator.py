from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class InsightGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, tipe: str, tanggal: date) -> dict:
        """Generate insight harian atau mingguan."""
        if tipe == "harian":
            return await self._generate_daily(tanggal)
        return await self._generate_weekly(tanggal)

    async def _generate_daily(self, tanggal: date) -> dict:
        """Generate insight harian dari data terkini."""
        # Get top rising commodities
        top_commodities = await self.db.execute(
            text("""
                SELECT
                    dc.nama_display,
                    ROUND(AVG(fpd.perubahan_mingguan)::numeric, 1) AS avg_weekly,
                    ROUND(AVG(fpd.harga)::numeric, 0) AS avg_harga
                FROM fact_price_daily fpd
                JOIN dim_commodity dc ON dc.id = fpd.commodity_id
                WHERE fpd.tanggal = :tanggal
                GROUP BY dc.nama_display
                ORDER BY avg_weekly DESC NULLS LAST
                LIMIT 3
            """),
            {"tanggal": tanggal},
        )
        top_comm = top_commodities.fetchall()

        # Get top pressure regions
        top_regions = await self.db.execute(
            text("""
                SELECT
                    dr.nama_provinsi,
                    ROUND(AVG(fpd.perubahan_mingguan)::numeric, 1) AS avg_weekly
                FROM fact_price_daily fpd
                JOIN dim_region dr ON dr.id = fpd.region_id
                WHERE fpd.tanggal = :tanggal AND dr.level_wilayah = 'provinsi'
                GROUP BY dr.nama_provinsi
                ORDER BY avg_weekly DESC NULLS LAST
                LIMIT 3
            """),
            {"tanggal": tanggal},
        )
        top_reg = top_regions.fetchall()

        # Get active alert count
        alert_count = await self.db.execute(
            text("SELECT COUNT(*) AS cnt FROM analytics_alerts WHERE is_active = TRUE")
        )
        alerts = alert_count.scalar()

        # Build insight content
        lines = [f"INSIGHT HARIAN — {tanggal.strftime('%A, %d %B %Y')}", ""]

        if top_comm:
            lines.append("KOMODITAS PERLU DIPERHATIKAN:")
            for row in top_comm:
                direction = "naik" if (row.avg_weekly or 0) > 0 else "turun"
                lines.append(
                    f"- {row.nama_display}: Rp {row.avg_harga:,.0f} "
                    f"({direction} {abs(row.avg_weekly or 0)}% mingguan)"
                )
            lines.append("")

        if top_reg:
            lines.append("WILAYAH PERLU DIPERHATIKAN:")
            for row in top_reg:
                lines.append(f"- {row.nama_provinsi}: rata-rata kenaikan {row.avg_weekly}%")
            lines.append("")

        if alerts and alerts > 0:
            lines.append(f"ALERT AKTIF: {alerts} alert memerlukan perhatian.")

        konten = "\n".join(lines)
        judul = f"Insight Harian {tanggal.isoformat()}"

        # Save insight
        await self.db.execute(
            text("""
                INSERT INTO analytics_insights (tanggal, tipe, judul, konten)
                VALUES (:tanggal, 'harian', :judul, :konten)
            """),
            {"tanggal": tanggal, "judul": judul, "konten": konten},
        )
        await self.db.commit()

        return {"tanggal": tanggal.isoformat(), "tipe": "harian", "judul": judul, "konten": konten}

    async def _generate_weekly(self, tanggal: date) -> dict:
        """Generate insight mingguan. Placeholder — diperkaya post-MVP."""
        judul = f"Ringkasan Mingguan {tanggal.isoformat()}"
        konten = f"Ringkasan mingguan untuk periode yang berakhir {tanggal.isoformat()}. (Konten akan di-generate oleh AI.)"

        await self.db.execute(
            text("""
                INSERT INTO analytics_insights (tanggal, tipe, judul, konten)
                VALUES (:tanggal, 'mingguan', :judul, :konten)
            """),
            {"tanggal": tanggal, "judul": judul, "konten": konten},
        )
        await self.db.commit()

        return {"tanggal": tanggal.isoformat(), "tipe": "mingguan", "judul": judul, "konten": konten}

    async def get_latest(self, tipe: str) -> dict | None:
        """Get insight terbaru."""
        result = await self.db.execute(
            text("""
                SELECT id, tanggal, tipe, judul, konten, data_snapshot, created_at
                FROM analytics_insights
                WHERE tipe = :tipe
                ORDER BY tanggal DESC
                LIMIT 1
            """),
            {"tipe": tipe},
        )
        row = result.fetchone()
        if not row:
            return None
        return dict(row._mapping)
