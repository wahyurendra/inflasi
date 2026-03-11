"""
Runner CLI untuk ETL pipeline PIHPS BI.

Penggunaan:
  python run_etl.py                      # hari ini
  python run_etl.py --date 2026-03-10    # tanggal spesifik
  python run_etl.py --days 7             # 7 hari ke belakang
  python run_etl.py --verbose            # tampilkan log detail
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import date, timedelta

# Tambah path analytics ke sys.path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"
)


async def run_pipeline(target_date: date, db: AsyncSession, verbose: bool = False) -> bool:
    from app.etl.pipelines.pihps_bi import PIHPSPipeline

    pipeline = PIHPSPipeline(db=db, target_date=target_date)
    try:
        print(f"\n{'='*60}")
        print(f"  ETL PIHPS BI — {target_date}")
        print(f"{'='*60}")

        print("  [1/4] Extracting from BI API...")
        raw = await pipeline.extract()
        print(f"        → {len(raw)} baris mentah")

        if not raw:
            print("  ✗ Tidak ada data. Skip.")
            return False

        print("  [2/4] Validating...")
        valid = await pipeline.validate(raw)
        if not valid:
            print("  ✗ Validasi gagal. Skip.")
            return False
        print("        → OK")

        print("  [3/4] Transforming...")
        clean = await pipeline.transform(raw)
        print(f"        → {len(clean)} records bersih")

        print("  [4/4] Loading ke database...")
        await pipeline.load(clean)
        print(f"  ✓ Selesai. {len(clean)} records dimuat.")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False
    finally:
        await pipeline.close()


async def main():
    parser = argparse.ArgumentParser(description="ETL PIHPS BI Runner")
    parser.add_argument("--date", type=str, help="Tanggal target (YYYY-MM-DD), default: hari ini")
    parser.add_argument("--days", type=int, default=1, help="Jumlah hari ke belakang")
    parser.add_argument("--verbose", "-v", action="store_true", help="Log detail")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # Tentukan daftar tanggal
    if args.date:
        dates = [date.fromisoformat(args.date)]
    else:
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(args.days - 1, -1, -1)]

    print(f"\nInflasi ETL Runner")
    print(f"Database: {DATABASE_URL.split('@')[-1]}")
    print(f"Tanggal  : {', '.join(str(d) for d in dates)}")

    # Setup DB
    engine = create_async_engine(DATABASE_URL, echo=args.verbose)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    success_count = 0
    async with session_factory() as db:
        for d in dates:
            ok = await run_pipeline(d, db, verbose=args.verbose)
            if ok:
                success_count += 1

    await engine.dispose()

    print(f"\n{'='*60}")
    print(f"  Hasil: {success_count}/{len(dates)} tanggal berhasil dimuat")
    print(f"{'='*60}\n")

    if success_count == 0 and len(dates) > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
