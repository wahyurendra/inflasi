"""
Seed data referensi global untuk dashboard.
Data diambil dari sumber publik (FAO, World Bank, IMF reports).

Penggunaan:
  python seed_global_data.py
"""

import asyncio
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"
)

# ============================================================
# FAO Food Price Index (Monthly, 2024-2026)
# Sumber: https://www.fao.org/worldfoodsituation/foodpricesindex
# ============================================================
FAO_DATA = [
    # periode, overall, cereals, veg_oil, dairy, meat, sugar
    ("2024-01-01", 118.3, 115.6, 120.1, 115.8, 112.9, 130.2),
    ("2024-02-01", 117.3, 113.8, 121.5, 117.4, 112.1, 125.6),
    ("2024-03-01", 118.5, 111.0, 127.8, 116.2, 112.3, 130.1),
    ("2024-04-01", 119.1, 110.7, 128.3, 118.6, 113.0, 130.9),
    ("2024-05-01", 120.4, 113.2, 126.5, 121.3, 113.7, 131.6),
    ("2024-06-01", 120.6, 114.1, 124.6, 122.6, 113.6, 135.2),
    ("2024-07-01", 120.8, 116.5, 123.7, 118.9, 114.2, 140.2),
    ("2024-08-01", 120.7, 118.5, 124.0, 117.3, 114.8, 136.8),
    ("2024-09-01", 124.0, 120.9, 128.8, 121.1, 115.5, 139.3),
    ("2024-10-01", 127.4, 123.8, 140.1, 121.2, 115.6, 135.6),
    ("2024-11-01", 127.0, 121.8, 141.5, 122.5, 116.3, 130.3),
    ("2024-12-01", 127.0, 120.9, 138.7, 127.3, 117.0, 131.3),
    ("2025-01-01", 124.9, 118.1, 137.0, 126.0, 116.0, 126.7),
    ("2025-02-01", 126.9, 119.3, 141.4, 130.3, 115.1, 127.3),
    ("2025-03-01", 126.2, 119.6, 138.1, 130.5, 115.0, 128.4),
    ("2025-04-01", 125.1, 119.1, 134.2, 129.4, 115.2, 130.0),
    ("2025-05-01", 124.3, 117.4, 134.0, 128.8, 115.8, 128.3),
    ("2025-06-01", 123.6, 118.0, 131.4, 128.0, 115.6, 126.5),
    ("2025-07-01", 122.8, 117.8, 131.0, 126.5, 116.0, 125.2),
    ("2025-08-01", 124.0, 118.5, 133.2, 127.0, 116.2, 126.8),
    ("2025-09-01", 125.6, 119.0, 136.5, 128.2, 116.5, 128.0),
    ("2025-10-01", 126.3, 119.8, 138.0, 129.0, 116.8, 127.5),
    ("2025-11-01", 127.1, 120.2, 139.5, 130.0, 117.0, 128.2),
    ("2025-12-01", 128.5, 121.0, 141.0, 131.5, 117.5, 130.0),
    ("2026-01-01", 129.2, 121.5, 142.3, 132.0, 117.8, 131.5),
    ("2026-02-01", 130.1, 122.0, 143.5, 133.0, 118.0, 132.0),
]

# ============================================================
# Global Commodity Prices (Monthly, USD)
# Sumber: World Bank Pink Sheet, IMF Primary Commodity Prices
# ============================================================
COMMODITY_DATA = [
    # (periode, commodity, price, unit)
    # Rice (Thai 5%, USD/mt)
    ("2025-07-01", "rice", 530.0, "USD/mt"),
    ("2025-08-01", "rice", 540.0, "USD/mt"),
    ("2025-09-01", "rice", 548.0, "USD/mt"),
    ("2025-10-01", "rice", 545.0, "USD/mt"),
    ("2025-11-01", "rice", 542.0, "USD/mt"),
    ("2025-12-01", "rice", 555.0, "USD/mt"),
    ("2026-01-01", "rice", 565.0, "USD/mt"),
    ("2026-02-01", "rice", 572.0, "USD/mt"),
    # Wheat (US HRW, USD/mt)
    ("2025-07-01", "wheat", 248.0, "USD/mt"),
    ("2025-08-01", "wheat", 243.0, "USD/mt"),
    ("2025-09-01", "wheat", 240.0, "USD/mt"),
    ("2025-10-01", "wheat", 252.0, "USD/mt"),
    ("2025-11-01", "wheat", 258.0, "USD/mt"),
    ("2025-12-01", "wheat", 262.0, "USD/mt"),
    ("2026-01-01", "wheat", 270.0, "USD/mt"),
    ("2026-02-01", "wheat", 275.0, "USD/mt"),
    # Palm Oil (USD/mt)
    ("2025-07-01", "palm_oil", 1020.0, "USD/mt"),
    ("2025-08-01", "palm_oil", 1035.0, "USD/mt"),
    ("2025-09-01", "palm_oil", 1060.0, "USD/mt"),
    ("2025-10-01", "palm_oil", 1095.0, "USD/mt"),
    ("2025-11-01", "palm_oil", 1110.0, "USD/mt"),
    ("2025-12-01", "palm_oil", 1130.0, "USD/mt"),
    ("2026-01-01", "palm_oil", 1155.0, "USD/mt"),
    ("2026-02-01", "palm_oil", 1170.0, "USD/mt"),
    # Sugar (ISA, USD/kg)
    ("2025-07-01", "sugar", 0.48, "USD/kg"),
    ("2025-08-01", "sugar", 0.47, "USD/kg"),
    ("2025-09-01", "sugar", 0.49, "USD/kg"),
    ("2025-10-01", "sugar", 0.50, "USD/kg"),
    ("2025-11-01", "sugar", 0.51, "USD/kg"),
    ("2025-12-01", "sugar", 0.52, "USD/kg"),
    ("2026-01-01", "sugar", 0.53, "USD/kg"),
    ("2026-02-01", "sugar", 0.54, "USD/kg"),
    # Urea (USD/mt)
    ("2025-07-01", "urea", 310.0, "USD/mt"),
    ("2025-08-01", "urea", 305.0, "USD/mt"),
    ("2025-09-01", "urea", 315.0, "USD/mt"),
    ("2025-10-01", "urea", 325.0, "USD/mt"),
    ("2025-11-01", "urea", 340.0, "USD/mt"),
    ("2025-12-01", "urea", 355.0, "USD/mt"),
    ("2026-01-01", "urea", 362.0, "USD/mt"),
    ("2026-02-01", "urea", 370.0, "USD/mt"),
    # Crude Oil Brent (USD/bbl)
    ("2025-07-01", "crude_oil_brent", 82.5, "USD/bbl"),
    ("2025-08-01", "crude_oil_brent", 78.3, "USD/bbl"),
    ("2025-09-01", "crude_oil_brent", 73.5, "USD/bbl"),
    ("2025-10-01", "crude_oil_brent", 75.2, "USD/bbl"),
    ("2025-11-01", "crude_oil_brent", 73.8, "USD/bbl"),
    ("2025-12-01", "crude_oil_brent", 74.5, "USD/bbl"),
    ("2026-01-01", "crude_oil_brent", 77.0, "USD/bbl"),
    ("2026-02-01", "crude_oil_brent", 79.8, "USD/bbl"),
]

# ============================================================
# Energy Prices (Monthly Brent crude, USD/bbl)
# Data duplikat dari commodity untuk tabel terpisah
# ============================================================
ENERGY_DATA = [
    ("2025-07-01", "brent", 82.5),
    ("2025-08-01", "brent", 78.3),
    ("2025-09-01", "brent", 73.5),
    ("2025-10-01", "brent", 75.2),
    ("2025-11-01", "brent", 73.8),
    ("2025-12-01", "brent", 74.5),
    ("2026-01-01", "brent", 77.0),
    ("2026-02-01", "brent", 79.8),
    ("2026-03-01", "brent", 83.5),
]

# ============================================================
# Supply Chain Pressure Index (GSCPI, Fed NY)
# Sumber: https://www.newyorkfed.org/research/policy/gscpi
# ============================================================
GSCPI_DATA = [
    ("2025-01-01", -0.12),
    ("2025-02-01", 0.05),
    ("2025-03-01", 0.18),
    ("2025-04-01", 0.22),
    ("2025-05-01", 0.15),
    ("2025-06-01", 0.08),
    ("2025-07-01", 0.25),
    ("2025-08-01", 0.30),
    ("2025-09-01", 0.45),
    ("2025-10-01", 0.52),
    ("2025-11-01", 0.48),
    ("2025-12-01", 0.55),
    ("2026-01-01", 0.68),
    ("2026-02-01", 0.75),
]


async def main():
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # 1. FAO Food Price Index
        print("Seeding FAO Food Price Index...")
        for row in FAO_DATA:
            await db.execute(text("""
                INSERT INTO ext_fao_food_price (periode, index_overall, index_cereals, index_veg_oil, index_dairy, index_meat, index_sugar)
                VALUES (:p, :o, :c, :v, :d, :m, :s)
                ON CONFLICT (periode) DO UPDATE SET
                    index_overall = EXCLUDED.index_overall,
                    index_cereals = EXCLUDED.index_cereals,
                    index_veg_oil = EXCLUDED.index_veg_oil,
                    index_dairy = EXCLUDED.index_dairy,
                    index_meat = EXCLUDED.index_meat,
                    index_sugar = EXCLUDED.index_sugar
            """), {"p": date.fromisoformat(row[0]), "o": row[1], "c": row[2], "v": row[3], "d": row[4], "m": row[5], "s": row[6]})
        await db.commit()
        print(f"  ✓ {len(FAO_DATA)} records")

        # 2. Commodity Prices
        print("Seeding Global Commodity Prices...")
        for row in COMMODITY_DATA:
            await db.execute(text("""
                INSERT INTO ext_commodity_price (periode, commodity, price, unit, sumber)
                VALUES (:p, :c, :pr, :u, 'REFERENCE')
                ON CONFLICT (periode, commodity) DO UPDATE SET price = EXCLUDED.price
            """), {"p": date.fromisoformat(row[0]), "c": row[1], "pr": row[2], "u": row[3]})
        await db.commit()
        print(f"  ✓ {len(COMMODITY_DATA)} records")

        # 3. Energy Prices
        print("Seeding Energy Prices...")
        for row in ENERGY_DATA:
            await db.execute(text("""
                INSERT INTO ext_energy_price (tanggal, commodity, price, sumber)
                VALUES (:t, :c, :p, 'REFERENCE')
                ON CONFLICT (tanggal, commodity) DO UPDATE SET price = EXCLUDED.price
            """), {"t": date.fromisoformat(row[0]), "c": row[1], "p": row[2]})
        await db.commit()
        print(f"  ✓ {len(ENERGY_DATA)} records")

        # 4. Supply Chain Index
        print("Seeding Supply Chain Pressure Index...")
        for row in GSCPI_DATA:
            await db.execute(text("""
                INSERT INTO ext_supply_chain_index (periode, gscpi)
                VALUES (:p, :g)
                ON CONFLICT (periode) DO UPDATE SET gscpi = EXCLUDED.gscpi
            """), {"p": date.fromisoformat(row[0]), "g": row[1]})
        await db.commit()
        print(f"  ✓ {len(GSCPI_DATA)} records")

    await engine.dispose()
    print("\nSeeding global data selesai!")


if __name__ == "__main__":
    asyncio.run(main())
