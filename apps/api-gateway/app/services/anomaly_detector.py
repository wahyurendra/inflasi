"""
Anomaly Detection Service menggunakan Isolation Forest.

Mendeteksi lonjakan harga abnormal berdasarkan:
- Perubahan harian dan mingguan
- Deviasi dari median wilayah
- Standar deviasi 14 hari
"""

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_anomalies(self, tanggal: date) -> int:
        """Run anomaly detection for all commodity-region pairs on given date."""
        # Get feature matrix
        features = await self._build_features(tanggal)
        if not features:
            logger.warning(f"No data for anomaly detection on {tanggal}")
            return 0

        try:
            from sklearn.ensemble import IsolationForest
            import numpy as np

            # Build feature matrix
            X = np.array([
                [
                    f["perubahan_harian"],
                    f["perubahan_mingguan"],
                    f["deviasi_wilayah"],
                    f["std_14d"],
                ]
                for f in features
            ])

            # Fit Isolation Forest
            model = IsolationForest(
                n_estimators=100,
                contamination=0.1,  # expect ~10% anomalies
                random_state=42,
            )
            model.fit(X)

            # Get anomaly scores (-1 = anomaly, 1 = normal)
            labels = model.predict(X)
            scores = model.decision_function(X)

            # Normalize scores to 0-1 range (0 = most anomalous)
            min_score = scores.min()
            max_score = scores.max()
            score_range = max_score - min_score if max_score != min_score else 1
            normalized = (scores - min_score) / score_range

        except ImportError:
            logger.warning("scikit-learn not installed, using z-score fallback")
            labels, normalized = self._zscore_fallback(features)

        # Store results
        count = 0
        for i, f in enumerate(features):
            is_anomaly = bool(labels[i] == -1) if hasattr(labels, '__getitem__') else False
            score = float(normalized[i]) if hasattr(normalized, '__getitem__') else 0.5

            await self.db.execute(
                text("""
                    INSERT INTO analytics_anomaly
                        (tanggal, region_id, commodity_id, anomaly_score, is_anomaly, features)
                    VALUES
                        (:tanggal, :region_id, :commodity_id, :score, :is_anomaly, :features::jsonb)
                    ON CONFLICT (tanggal, region_id, commodity_id)
                    DO UPDATE SET
                        anomaly_score = EXCLUDED.anomaly_score,
                        is_anomaly = EXCLUDED.is_anomaly,
                        features = EXCLUDED.features
                """),
                {
                    "tanggal": tanggal,
                    "region_id": f["region_id"],
                    "commodity_id": f["commodity_id"],
                    "score": round(score, 4),
                    "is_anomaly": is_anomaly,
                    "features": str({
                        "perubahan_harian": f["perubahan_harian"],
                        "perubahan_mingguan": f["perubahan_mingguan"],
                        "deviasi_wilayah": f["deviasi_wilayah"],
                        "std_14d": f["std_14d"],
                    }).replace("'", '"'),
                },
            )
            if is_anomaly:
                count += 1

        await self.db.commit()
        logger.info(f"Detected {count} anomalies out of {len(features)} pairs on {tanggal}")
        return count

    async def _build_features(self, tanggal: date) -> list[dict]:
        """Build feature matrix for anomaly detection."""
        query = text("""
            WITH current_prices AS (
                SELECT
                    commodity_id, region_id, harga,
                    COALESCE(perubahan_harian, 0) AS perubahan_harian,
                    COALESCE(perubahan_mingguan, 0) AS perubahan_mingguan
                FROM fact_price_daily
                WHERE tanggal = :tanggal
            ),
            median_prices AS (
                SELECT
                    commodity_id,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY harga) AS median_harga
                FROM fact_price_daily
                WHERE tanggal = :tanggal
                GROUP BY commodity_id
            ),
            price_std AS (
                SELECT
                    commodity_id, region_id,
                    COALESCE(STDDEV(harga), 0) AS std_14d
                FROM fact_price_daily
                WHERE tanggal BETWEEN :start_14d AND :tanggal
                GROUP BY commodity_id, region_id
            )
            SELECT
                cp.commodity_id,
                cp.region_id,
                cp.perubahan_harian,
                cp.perubahan_mingguan,
                CASE WHEN mp.median_harga > 0
                    THEN ((cp.harga - mp.median_harga) / mp.median_harga * 100)
                    ELSE 0
                END AS deviasi_wilayah,
                COALESCE(ps.std_14d, 0) AS std_14d
            FROM current_prices cp
            LEFT JOIN median_prices mp ON mp.commodity_id = cp.commodity_id
            LEFT JOIN price_std ps ON ps.commodity_id = cp.commodity_id AND ps.region_id = cp.region_id
        """)

        result = await self.db.execute(
            query,
            {"tanggal": tanggal, "start_14d": tanggal - timedelta(days=14)},
        )

        return [
            {
                "commodity_id": row.commodity_id,
                "region_id": row.region_id,
                "perubahan_harian": float(row.perubahan_harian),
                "perubahan_mingguan": float(row.perubahan_mingguan),
                "deviasi_wilayah": float(row.deviasi_wilayah),
                "std_14d": float(row.std_14d),
            }
            for row in result.fetchall()
        ]

    def _zscore_fallback(self, features: list[dict]) -> tuple:
        """Simple z-score based anomaly detection when sklearn unavailable."""
        import statistics

        daily_changes = [f["perubahan_harian"] for f in features]
        weekly_changes = [f["perubahan_mingguan"] for f in features]

        if len(daily_changes) < 3:
            return [-1] * len(features), [0.5] * len(features)

        mean_d = statistics.mean(daily_changes)
        std_d = statistics.stdev(daily_changes) if len(daily_changes) > 1 else 1
        mean_w = statistics.mean(weekly_changes)
        std_w = statistics.stdev(weekly_changes) if len(weekly_changes) > 1 else 1

        labels = []
        scores = []
        for f in features:
            z_d = abs((f["perubahan_harian"] - mean_d) / std_d) if std_d > 0 else 0
            z_w = abs((f["perubahan_mingguan"] - mean_w) / std_w) if std_w > 0 else 0
            z_combined = (z_d + z_w) / 2

            is_anomaly = z_combined > 2.0
            labels.append(-1 if is_anomaly else 1)
            scores.append(min(1.0, z_combined / 4.0))

        return labels, scores

    async def get_anomalies(self, tanggal: date, only_anomalies: bool = True) -> list[dict]:
        """Get anomaly results for a given date."""
        where = "AND aa.is_anomaly = TRUE" if only_anomalies else ""
        query = text(f"""
            SELECT
                aa.tanggal, aa.anomaly_score, aa.is_anomaly, aa.features,
                dr.nama_provinsi, dr.kode_wilayah,
                dc.nama_display, dc.kode_komoditas
            FROM analytics_anomaly aa
            JOIN dim_region dr ON dr.id = aa.region_id
            JOIN dim_commodity dc ON dc.id = aa.commodity_id
            WHERE aa.tanggal = :tanggal {where}
            ORDER BY aa.anomaly_score ASC
        """)

        result = await self.db.execute(query, {"tanggal": tanggal})
        return [dict(row._mapping) for row in result.fetchall()]
