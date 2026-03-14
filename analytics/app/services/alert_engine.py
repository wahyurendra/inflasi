from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# Threshold constants (match src/lib/constants.ts)
PRICE_SPIKE_7D_PCT = 10
PRICE_RISE_7D_PCT = 5
REGIONAL_DEVIATION_PCT = 20
VOLATILITY_CV_14D = 15
WEATHER_PRICE_COMBO_PCT = 3
MULTI_COMMODITY_COUNT = 3
MULTI_COMMODITY_PCT = 5


class AlertEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_daily(self, tanggal: date) -> int:
        """Jalankan semua alert rules dan simpan hasilnya."""
        alerts = []

        alerts.extend(await self._check_price_spike(tanggal))
        alerts.extend(await self._check_price_rise(tanggal))
        alerts.extend(await self._check_regional_deviation(tanggal))
        alerts.extend(await self._check_sustained_volatility(tanggal))
        alerts.extend(await self._check_multi_commodity(tanggal))
        alerts.extend(await self._check_weather_price_combo(tanggal))

        # Simpan alerts
        for alert in alerts:
            await self.db.execute(
                text("""
                    INSERT INTO analytics_alerts
                        (tanggal, region_id, commodity_id, alert_type, severity, judul, deskripsi, nilai_aktual, nilai_threshold)
                    VALUES
                        (:tanggal, :region_id, :commodity_id, :alert_type, :severity, :judul, :deskripsi, :nilai_aktual, :nilai_threshold)
                    ON CONFLICT DO NOTHING
                """),
                alert,
            )

        # Auto-resolve old alerts
        await self._auto_resolve(tanggal)
        await self.db.commit()

        return len(alerts)

    async def _check_price_spike(self, tanggal: date) -> list[dict]:
        """R1: Harga naik >10% dalam 7 hari → critical."""
        query = text("""
            SELECT
                fpd.region_id, fpd.commodity_id,
                dr.nama_provinsi, dc.nama_display,
                fpd.harga AS harga_now,
                prev.harga AS harga_7d_ago,
                ROUND(((fpd.harga - prev.harga) / prev.harga * 100)::numeric, 2) AS pct_change
            FROM fact_price_daily fpd
            JOIN fact_price_daily prev
                ON prev.commodity_id = fpd.commodity_id
                AND prev.region_id = fpd.region_id
                AND prev.tanggal = :week_ago
            JOIN dim_region dr ON dr.id = fpd.region_id
            JOIN dim_commodity dc ON dc.id = fpd.commodity_id
            WHERE fpd.tanggal = :tanggal
              AND prev.harga > 0
              AND ((fpd.harga - prev.harga) / prev.harga * 100) > :threshold
        """)

        result = await self.db.execute(
            query,
            {"tanggal": tanggal, "week_ago": tanggal - timedelta(days=7), "threshold": PRICE_SPIKE_7D_PCT},
        )

        alerts = []
        for row in result.fetchall():
            alerts.append({
                "tanggal": tanggal,
                "region_id": row.region_id,
                "commodity_id": row.commodity_id,
                "alert_type": "price_spike",
                "severity": "critical",
                "judul": f"{row.nama_display}: Kenaikan {row.pct_change}% dalam 7 hari di {row.nama_provinsi}",
                "deskripsi": (
                    f"Harga {row.nama_display} di {row.nama_provinsi} naik {row.pct_change}% "
                    f"dalam 7 hari terakhir (dari Rp {row.harga_7d_ago:,.0f} ke Rp {row.harga_now:,.0f}). "
                    f"Threshold: >{PRICE_SPIKE_7D_PCT}%."
                ),
                "nilai_aktual": float(row.pct_change),
                "nilai_threshold": float(PRICE_SPIKE_7D_PCT),
            })
        return alerts

    async def _check_price_rise(self, tanggal: date) -> list[dict]:
        """R2: Harga naik >5% dalam 7 hari → warning."""
        query = text("""
            SELECT
                fpd.region_id, fpd.commodity_id,
                dr.nama_provinsi, dc.nama_display,
                fpd.harga AS harga_now,
                prev.harga AS harga_7d_ago,
                ROUND(((fpd.harga - prev.harga) / prev.harga * 100)::numeric, 2) AS pct_change
            FROM fact_price_daily fpd
            JOIN fact_price_daily prev
                ON prev.commodity_id = fpd.commodity_id
                AND prev.region_id = fpd.region_id
                AND prev.tanggal = :week_ago
            JOIN dim_region dr ON dr.id = fpd.region_id
            JOIN dim_commodity dc ON dc.id = fpd.commodity_id
            WHERE fpd.tanggal = :tanggal
              AND prev.harga > 0
              AND ((fpd.harga - prev.harga) / prev.harga * 100) BETWEEN :low AND :high
        """)

        result = await self.db.execute(
            query,
            {
                "tanggal": tanggal,
                "week_ago": tanggal - timedelta(days=7),
                "low": PRICE_RISE_7D_PCT,
                "high": PRICE_SPIKE_7D_PCT,
            },
        )

        alerts = []
        for row in result.fetchall():
            alerts.append({
                "tanggal": tanggal,
                "region_id": row.region_id,
                "commodity_id": row.commodity_id,
                "alert_type": "price_rise",
                "severity": "warning",
                "judul": f"{row.nama_display}: Naik {row.pct_change}% dalam 7 hari di {row.nama_provinsi}",
                "deskripsi": (
                    f"Harga {row.nama_display} di {row.nama_provinsi} naik {row.pct_change}% "
                    f"dalam 7 hari terakhir (dari Rp {row.harga_7d_ago:,.0f} ke Rp {row.harga_now:,.0f})."
                ),
                "nilai_aktual": float(row.pct_change),
                "nilai_threshold": float(PRICE_RISE_7D_PCT),
            })
        return alerts

    async def _check_regional_deviation(self, tanggal: date) -> list[dict]:
        """R3: Harga wilayah >20% di atas median nasional → warning."""
        query = text("""
            WITH median_prices AS (
                SELECT
                    commodity_id,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY harga) AS median_harga
                FROM fact_price_daily
                WHERE tanggal = :tanggal
                GROUP BY commodity_id
            )
            SELECT
                fpd.region_id, fpd.commodity_id,
                dr.nama_provinsi, dc.nama_display,
                fpd.harga,
                mp.median_harga,
                ROUND(((fpd.harga - mp.median_harga) / mp.median_harga * 100)::numeric, 2) AS deviation_pct
            FROM fact_price_daily fpd
            JOIN median_prices mp ON mp.commodity_id = fpd.commodity_id
            JOIN dim_region dr ON dr.id = fpd.region_id
            JOIN dim_commodity dc ON dc.id = fpd.commodity_id
            WHERE fpd.tanggal = :tanggal
              AND mp.median_harga > 0
              AND ((fpd.harga - mp.median_harga) / mp.median_harga * 100) > :threshold
              AND dr.level_wilayah = 'provinsi'
        """)

        result = await self.db.execute(
            query, {"tanggal": tanggal, "threshold": REGIONAL_DEVIATION_PCT}
        )

        alerts = []
        for row in result.fetchall():
            alerts.append({
                "tanggal": tanggal,
                "region_id": row.region_id,
                "commodity_id": row.commodity_id,
                "alert_type": "deviation",
                "severity": "warning",
                "judul": f"{row.nama_display} di {row.nama_provinsi}: {row.deviation_pct}% di atas median nasional",
                "deskripsi": (
                    f"Harga {row.nama_display} di {row.nama_provinsi} (Rp {row.harga:,.0f}) "
                    f"berada {row.deviation_pct}% di atas median nasional (Rp {row.median_harga:,.0f})."
                ),
                "nilai_aktual": float(row.deviation_pct),
                "nilai_threshold": float(REGIONAL_DEVIATION_PCT),
            })
        return alerts

    async def _check_sustained_volatility(self, tanggal: date) -> list[dict]:
        """R4: CV >15% selama 14 hari berturut-turut → warning."""
        query = text("""
            WITH price_stats AS (
                SELECT
                    commodity_id, region_id,
                    STDDEV(harga) / NULLIF(AVG(harga), 0) * 100 AS cv
                FROM fact_price_daily
                WHERE tanggal BETWEEN :start_date AND :end_date
                GROUP BY commodity_id, region_id
                HAVING COUNT(*) >= 10
            )
            SELECT
                ps.region_id, ps.commodity_id,
                dr.nama_provinsi, dc.nama_display,
                ROUND(ps.cv::numeric, 2) AS cv
            FROM price_stats ps
            JOIN dim_region dr ON dr.id = ps.region_id
            JOIN dim_commodity dc ON dc.id = ps.commodity_id
            WHERE ps.cv > :threshold
        """)

        result = await self.db.execute(
            query,
            {
                "start_date": tanggal - timedelta(days=14),
                "end_date": tanggal,
                "threshold": VOLATILITY_CV_14D,
            },
        )

        alerts = []
        for row in result.fetchall():
            alerts.append({
                "tanggal": tanggal,
                "region_id": row.region_id,
                "commodity_id": row.commodity_id,
                "alert_type": "sustained_volatile",
                "severity": "warning",
                "judul": f"{row.nama_display}: Volatilitas tinggi (CV {row.cv}%) di {row.nama_provinsi}",
                "deskripsi": (
                    f"{row.nama_display} di {row.nama_provinsi} menunjukkan volatilitas tinggi "
                    f"selama 14 hari terakhir (CV: {row.cv}%, threshold: {VOLATILITY_CV_14D}%)."
                ),
                "nilai_aktual": float(row.cv),
                "nilai_threshold": float(VOLATILITY_CV_14D),
            })
        return alerts

    async def _check_multi_commodity(self, tanggal: date) -> list[dict]:
        """R6: >=3 komoditas naik >5% di 1 wilayah bersamaan → critical."""
        query = text("""
            WITH rising AS (
                SELECT
                    fpd.region_id,
                    fpd.commodity_id,
                    ROUND(((fpd.harga - prev.harga) / prev.harga * 100)::numeric, 2) AS pct_change
                FROM fact_price_daily fpd
                JOIN fact_price_daily prev
                    ON prev.commodity_id = fpd.commodity_id
                    AND prev.region_id = fpd.region_id
                    AND prev.tanggal = :week_ago
                WHERE fpd.tanggal = :tanggal
                  AND prev.harga > 0
                  AND ((fpd.harga - prev.harga) / prev.harga * 100) > :threshold
            ),
            region_counts AS (
                SELECT region_id, COUNT(*) AS rising_count
                FROM rising
                GROUP BY region_id
                HAVING COUNT(*) >= :min_count
            )
            SELECT
                rc.region_id,
                dr.nama_provinsi,
                rc.rising_count
            FROM region_counts rc
            JOIN dim_region dr ON dr.id = rc.region_id
            WHERE dr.level_wilayah = 'provinsi'
        """)

        result = await self.db.execute(
            query,
            {
                "tanggal": tanggal,
                "week_ago": tanggal - timedelta(days=7),
                "threshold": MULTI_COMMODITY_PCT,
                "min_count": MULTI_COMMODITY_COUNT,
            },
        )

        alerts = []
        for row in result.fetchall():
            # Use commodity_id=0 as a placeholder for multi-commodity alerts
            # We need a valid reference, so we'll use the first commodity
            alerts.append({
                "tanggal": tanggal,
                "region_id": row.region_id,
                "commodity_id": 1,  # placeholder
                "alert_type": "multi_commodity",
                "severity": "critical",
                "judul": f"{row.nama_provinsi}: {row.rising_count} komoditas naik >{MULTI_COMMODITY_PCT}% bersamaan",
                "deskripsi": (
                    f"Di {row.nama_provinsi}, {row.rising_count} komoditas mengalami kenaikan "
                    f">{MULTI_COMMODITY_PCT}% dalam 7 hari terakhir secara bersamaan."
                ),
                "nilai_aktual": float(row.rising_count),
                "nilai_threshold": float(MULTI_COMMODITY_COUNT),
            })
        return alerts

    async def _check_weather_price_combo(self, tanggal: date) -> list[dict]:
        """R5: Warning cuaca (siaga/awas) + harga naik >3% → critical."""
        query = text("""
            SELECT
                fpd.region_id, fpd.commodity_id,
                dr.nama_provinsi, dc.nama_display,
                fc.warning_level, fc.curah_hujan,
                ROUND(((fpd.harga - prev.harga) / prev.harga * 100)::numeric, 2) AS pct_change
            FROM fact_price_daily fpd
            JOIN fact_price_daily prev
                ON prev.commodity_id = fpd.commodity_id
                AND prev.region_id = fpd.region_id
                AND prev.tanggal = :week_ago
            JOIN fact_climate fc
                ON fc.region_id = fpd.region_id
                AND fc.tanggal = :tanggal
            JOIN dim_region dr ON dr.id = fpd.region_id
            JOIN dim_commodity dc ON dc.id = fpd.commodity_id
            WHERE fpd.tanggal = :tanggal
              AND prev.harga > 0
              AND fc.warning_level IN ('siaga', 'awas')
              AND ((fpd.harga - prev.harga) / prev.harga * 100) > :threshold
        """)

        result = await self.db.execute(
            query,
            {
                "tanggal": tanggal,
                "week_ago": tanggal - timedelta(days=7),
                "threshold": WEATHER_PRICE_COMBO_PCT,
            },
        )

        alerts = []
        for row in result.fetchall():
            curah = float(row.curah_hujan) if row.curah_hujan else 0
            alerts.append({
                "tanggal": tanggal,
                "region_id": row.region_id,
                "commodity_id": row.commodity_id,
                "alert_type": "weather_price_combo",
                "severity": "critical",
                "judul": (
                    f"{row.nama_display} di {row.nama_provinsi}: "
                    f"Cuaca {row.warning_level} + harga naik {row.pct_change}%"
                ),
                "deskripsi": (
                    f"Wilayah {row.nama_provinsi} mengalami kondisi cuaca level {row.warning_level} "
                    f"(curah hujan {curah:.0f}mm) bersamaan dengan kenaikan harga {row.nama_display} "
                    f"sebesar {row.pct_change}% dalam 7 hari terakhir."
                ),
                "nilai_aktual": float(row.pct_change),
                "nilai_threshold": float(WEATHER_PRICE_COMBO_PCT),
            })
        return alerts

    async def _auto_resolve(self, tanggal: date) -> None:
        """Auto-resolve alerts yang lebih dari 7 hari dan kondisinya sudah normal."""
        await self.db.execute(
            text("""
                UPDATE analytics_alerts
                SET is_active = FALSE, resolved_at = NOW()
                WHERE is_active = TRUE
                  AND tanggal < :cutoff
            """),
            {"cutoff": tanggal - timedelta(days=7)},
        )

    async def get_active_alerts(self, severity: str | None, limit: int) -> list[dict]:
        """Get daftar alert aktif."""
        where_clause = "WHERE aa.is_active = TRUE"
        params: dict = {"limit": limit}

        if severity:
            where_clause += " AND aa.severity = :severity"
            params["severity"] = severity

        query = text(f"""
            SELECT
                aa.id, aa.tanggal, aa.alert_type, aa.severity,
                aa.judul, aa.deskripsi, aa.nilai_aktual, aa.nilai_threshold,
                dr.nama_provinsi, dr.kode_wilayah,
                dc.nama_display, dc.kode_komoditas
            FROM analytics_alerts aa
            JOIN dim_region dr ON dr.id = aa.region_id
            JOIN dim_commodity dc ON dc.id = aa.commodity_id
            {where_clause}
            ORDER BY
                CASE aa.severity
                    WHEN 'critical' THEN 1
                    WHEN 'warning' THEN 2
                    ELSE 3
                END,
                aa.tanggal DESC
            LIMIT :limit
        """)

        result = await self.db.execute(query, params)
        return [dict(row._mapping) for row in result.fetchall()]

    async def resolve_alert(self, alert_id: int) -> None:
        await self.db.execute(
            text("UPDATE analytics_alerts SET is_active = FALSE, resolved_at = NOW() WHERE id = :id"),
            {"id": alert_id},
        )
        await self.db.commit()
