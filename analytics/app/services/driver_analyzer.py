"""
Driver Analysis Service — Root Cause Analysis.

Menjelaskan penyebab kenaikan harga berdasarkan faktor-faktor:
- Cuaca (curah hujan, warning level)
- Stok pangan (status supply)
- Kurs USD/IDR
- Musiman (Ramadan, Nataru, panen)
- Harga komoditas global
- Logistik (GSCPI proxy)

Untuk MVP menggunakan weighted heuristic, bukan SHAP.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Komoditas yang import-sensitive (terpengaruh kurs)
IMPORT_SENSITIVE = {"BAWANG_PUTIH", "GULA_PASIR", "MINYAK_GORENG"}

# Mapping komoditas lokal ke global
LOCAL_TO_GLOBAL = {
    "BERAS": "rice",
    "GULA_PASIR": "sugar",
    "MINYAK_GORENG": "palm_oil",
    "BAWANG_PUTIH": "wheat",  # proxy
}


class DriverAnalyzer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self, commodity_id: int, region_id: int, tanggal: date | None = None
    ) -> dict:
        """Analyze price drivers for a commodity-region pair."""
        tanggal = tanggal or date.today()

        # Gather signals from multiple tables
        cuaca = await self._get_weather_signal(region_id, tanggal)
        stok = await self._get_stock_signal(commodity_id, region_id, tanggal)
        kurs = await self._get_kurs_signal(tanggal)
        musiman = await self._get_seasonal_signal(tanggal)
        global_signal = await self._get_global_signal(commodity_id, tanggal)
        logistik = await self._get_logistics_signal(tanggal)

        # Get commodity info
        result = await self.db.execute(
            text("SELECT nama_display, kode_komoditas FROM dim_commodity WHERE id = :id"),
            {"id": commodity_id},
        )
        commodity_row = result.fetchone()
        kode = commodity_row.kode_komoditas if commodity_row else ""

        # Adjust weights based on commodity type
        is_import = kode in IMPORT_SENSITIVE
        weights = self._get_adjusted_weights(is_import)

        # Calculate contribution scores
        signals = {
            "cuaca": cuaca,
            "stok": stok,
            "kurs": kurs,
            "musiman": musiman,
            "global": global_signal,
            "logistik": logistik,
        }

        total_raw = sum(
            signals[k]["magnitude"] * weights[k] for k in signals
        )

        drivers = []
        for name, signal in signals.items():
            if total_raw > 0:
                contribution = (signal["magnitude"] * weights[name]) / total_raw * 100
            else:
                contribution = 0

            drivers.append({
                "name": name,
                "contribution_pct": round(contribution, 1),
                "magnitude": round(signal["magnitude"], 2),
                "direction": signal["direction"],
                "detail": signal["detail"],
            })

        # Sort by contribution descending
        drivers.sort(key=lambda d: d["contribution_pct"], reverse=True)

        return {
            "commodity_id": commodity_id,
            "region_id": region_id,
            "tanggal": str(tanggal),
            "commodity": commodity_row.nama_display if commodity_row else "",
            "drivers": drivers,
        }

    def _get_adjusted_weights(self, is_import: bool) -> dict:
        if is_import:
            return {
                "cuaca": 0.10,
                "stok": 0.15,
                "kurs": 0.30,
                "musiman": 0.15,
                "global": 0.20,
                "logistik": 0.10,
            }
        return {
            "cuaca": 0.30,
            "stok": 0.20,
            "kurs": 0.05,
            "musiman": 0.25,
            "global": 0.10,
            "logistik": 0.10,
        }

    async def _get_weather_signal(self, region_id: int, tanggal: date) -> dict:
        result = await self.db.execute(
            text("""
                SELECT curah_hujan, suhu_rata, warning_level
                FROM fact_climate
                WHERE region_id = :rid AND tanggal = :tanggal
            """),
            {"rid": region_id, "tanggal": tanggal},
        )
        row = result.fetchone()
        if not row:
            return {"magnitude": 0, "direction": "neutral", "detail": "Data cuaca tidak tersedia"}

        warning_scores = {"normal": 0, "waspada": 30, "siaga": 60, "awas": 100}
        score = warning_scores.get(row.warning_level or "normal", 0)
        rainfall = float(row.curah_hujan) if row.curah_hujan else 0

        direction = "naik" if score > 30 else "neutral"
        detail = f"Curah hujan {rainfall:.0f}mm, level {row.warning_level or 'normal'}"

        return {"magnitude": score, "direction": direction, "detail": detail}

    async def _get_stock_signal(self, commodity_id: int, region_id: int, tanggal: date) -> dict:
        result = await self.db.execute(
            text("""
                SELECT status, stok, cadangan
                FROM fact_supply_stock
                WHERE commodity_id = :cid AND region_id = :rid
                ORDER BY ABS(tanggal - :tanggal::date)
                LIMIT 1
            """),
            {"cid": commodity_id, "rid": region_id, "tanggal": tanggal},
        )
        row = result.fetchone()
        if not row:
            return {"magnitude": 0, "direction": "neutral", "detail": "Data stok tidak tersedia"}

        status_scores = {"aman": 0, "waspada": 50, "kritis": 100}
        score = status_scores.get(row.status or "aman", 0)
        direction = "naik" if score > 30 else "neutral"
        detail = f"Status stok: {row.status or 'aman'}"

        return {"magnitude": score, "direction": direction, "detail": detail}

    async def _get_kurs_signal(self, tanggal: date) -> dict:
        result = await self.db.execute(
            text("""
                SELECT kurs_tengah, change_pct
                FROM ext_exchange_rate
                WHERE tanggal <= :tanggal
                ORDER BY tanggal DESC
                LIMIT 1
            """),
            {"tanggal": tanggal},
        )
        row = result.fetchone()
        if not row:
            return {"magnitude": 0, "direction": "neutral", "detail": "Data kurs tidak tersedia"}

        change = float(row.change_pct) if row.change_pct else 0
        # Kurs naik (IDR melemah) = tekanan naik untuk barang impor
        score = min(100, abs(change) * 20)  # 5% change = score 100
        direction = "naik" if change > 0.5 else "turun" if change < -0.5 else "neutral"
        kurs_val = float(row.kurs_tengah) if row.kurs_tengah else 0
        detail = f"USD/IDR Rp {kurs_val:,.0f} ({'+' if change > 0 else ''}{change:.2f}%)"

        return {"magnitude": score, "direction": direction, "detail": detail}

    async def _get_seasonal_signal(self, tanggal: date) -> dict:
        result = await self.db.execute(
            text("""
                SELECT musim, nama_libur, is_hari_libur
                FROM dim_calendar
                WHERE tanggal = :tanggal
            """),
            {"tanggal": tanggal},
        )
        row = result.fetchone()
        if not row:
            return {"magnitude": 0, "direction": "neutral", "detail": "Normal"}

        musim = row.musim or "normal"
        season_scores = {
            "ramadan": 80,
            "idulfitri": 90,
            "nataru": 70,
            "paceklik": 60,
            "panen_raya": 20,  # panen = supply naik, tekanan turun
            "normal": 0,
        }
        score = season_scores.get(musim, 0)

        if row.is_hari_libur and score < 50:
            score = max(score, 40)

        direction = "naik" if score > 30 else "turun" if musim == "panen_raya" else "neutral"
        detail = f"Musim: {musim}"
        if row.nama_libur:
            detail += f" ({row.nama_libur})"

        return {"magnitude": score, "direction": direction, "detail": detail}

    async def _get_global_signal(self, commodity_id: int, tanggal: date) -> dict:
        # Get commodity code
        result = await self.db.execute(
            text("SELECT kode_komoditas FROM dim_commodity WHERE id = :id"),
            {"id": commodity_id},
        )
        row = result.fetchone()
        if not row:
            return {"magnitude": 0, "direction": "neutral", "detail": "N/A"}

        global_name = LOCAL_TO_GLOBAL.get(row.kode_komoditas)
        if not global_name:
            return {"magnitude": 0, "direction": "neutral", "detail": "Tidak ada pasangan global"}

        result = await self.db.execute(
            text("""
                SELECT price, change_pct
                FROM ext_commodity_price
                WHERE commodity = :commodity
                ORDER BY ABS(periode - :tanggal::date)
                LIMIT 1
            """),
            {"commodity": global_name, "tanggal": tanggal},
        )
        row = result.fetchone()
        if not row:
            return {"magnitude": 0, "direction": "neutral", "detail": "Data global tidak tersedia"}

        change = float(row.change_pct) if row.change_pct else 0
        score = min(100, abs(change) * 10)  # 10% change = score 100
        direction = "naik" if change > 1 else "turun" if change < -1 else "neutral"
        detail = f"{global_name}: ${float(row.price):,.0f} ({'+' if change > 0 else ''}{change:.1f}%)"

        return {"magnitude": score, "direction": direction, "detail": detail}

    async def _get_logistics_signal(self, tanggal: date) -> dict:
        result = await self.db.execute(
            text("""
                SELECT gscpi
                FROM ext_supply_chain_index
                ORDER BY ABS(periode - :tanggal::date)
                LIMIT 1
            """),
            {"tanggal": tanggal},
        )
        row = result.fetchone()
        if not row:
            return {"magnitude": 0, "direction": "neutral", "detail": "Data GSCPI tidak tersedia"}

        gscpi = float(row.gscpi)
        # GSCPI > 0 = pressure above average, normalize to 0-100
        score = min(100, max(0, (gscpi + 2) * 25))  # range -2 to +2 → 0 to 100
        direction = "naik" if gscpi > 0.5 else "turun" if gscpi < -0.5 else "neutral"
        detail = f"GSCPI: {gscpi:.2f} std dev"

        return {"magnitude": score, "direction": direction, "detail": detail}
