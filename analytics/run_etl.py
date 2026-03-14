"""
Runner CLI untuk semua ETL pipelines.

Penggunaan:
  python run_etl.py                           # semua pipeline, hari ini
  python run_etl.py --pipeline pihps          # hanya PIHPS BI
  python run_etl.py --pipeline pihps --days 7 # PIHPS 7 hari
  python run_etl.py --pipeline global         # semua global datasets
  python run_etl.py --pipeline news           # hanya GDELT news
  python run_etl.py --verbose                 # log detail

Pipelines:
  pihps   - Harga pangan harian dari PIHPS BI
  kurs    - Kurs USD/IDR dari ECB
  energy  - Harga energi (Brent crude)
  fao     - FAO Food Price Index
  commodity - Harga komoditas global (World Bank)
  news    - Berita intelligence (GDELT)
  bmkg    - Data cuaca BMKG
  global  - Semua global (kurs + energy + fao + commodity + news)
  all     - Semua pipeline
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"
)

PIPELINES = ["pihps", "kurs", "energy", "fao", "commodity", "news", "bmkg"]


async def run_pihps(db: AsyncSession, dates: list[date], verbose: bool) -> int:
    from app.etl.pipelines.pihps_bi import PIHPSPipeline

    success = 0
    for target_date in dates:
        pipeline = PIHPSPipeline(db=db, target_date=target_date)
        try:
            print(f"\n  PIHPS BI — {target_date}")
            raw = await pipeline.extract()
            print(f"    Extract: {len(raw)} baris")
            if not raw:
                continue
            valid = await pipeline.validate(raw)
            if not valid:
                print("    ✗ Validasi gagal")
                continue
            clean = await pipeline.transform(raw)
            await pipeline.load(clean)
            print(f"    ✓ {len(clean)} records dimuat")
            success += 1
        except Exception as e:
            print(f"    ✗ Error: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
        finally:
            await pipeline.close()
    return success


async def run_kurs(db: AsyncSession, days: int, verbose: bool) -> int:
    from app.etl.pipelines.exchange_rate import ExchangeRatePipeline

    end = date.today()
    start = end - timedelta(days=days)
    pipeline = ExchangeRatePipeline(db=db, start_date=start, end_date=end)
    print(f"\n  Kurs USD/IDR — {start} s/d {end}")
    count = await pipeline.run()
    print(f"    ✓ {count} records dimuat")
    return count


async def run_energy(db: AsyncSession, days: int, verbose: bool) -> int:
    from app.etl.pipelines.energy_price import EnergyPricePipeline

    pipeline = EnergyPricePipeline(db=db, days=days)
    print(f"\n  Energy Prices — last {days} days")
    count = await pipeline.run()
    print(f"    ✓ {count} records dimuat")
    return count


async def run_fao(db: AsyncSession, verbose: bool) -> int:
    from app.etl.pipelines.fao_food_price import FAOFoodPricePipeline

    pipeline = FAOFoodPricePipeline(db=db)
    print(f"\n  FAO Food Price Index")
    count = await pipeline.run()
    print(f"    ✓ {count} records dimuat")
    return count


async def run_commodity(db: AsyncSession, verbose: bool) -> int:
    from app.etl.pipelines.commodity_global import CommodityGlobalPipeline

    pipeline = CommodityGlobalPipeline(db=db, year_start=2023)
    print(f"\n  World Bank Commodity Prices")
    count = await pipeline.run()
    print(f"    ✓ {count} records dimuat")
    return count


async def run_news(db: AsyncSession, days: int, verbose: bool) -> int:
    from app.etl.pipelines.gdelt_news import GDELTNewsPipeline

    pipeline = GDELTNewsPipeline(db=db, days=days)
    print(f"\n  GDELT News Intelligence — last {days} days")
    count = await pipeline.run()
    print(f"    ✓ {count} articles dimuat")
    return count


async def run_bmkg(db: AsyncSession, dates: list[date], verbose: bool) -> int:
    from app.etl.pipelines.bmkg_weather import BMKGWeatherPipeline

    success = 0
    for target_date in dates:
        pipeline = BMKGWeatherPipeline(db=db, target_date=target_date)
        try:
            print(f"\n  BMKG Weather — {target_date}")
            result = await pipeline.run()
            print(f"    ✓ {result.get('records', 0)} records dimuat")
            success += 1
        except Exception as e:
            print(f"    ✗ Error: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
    return success


async def main():
    parser = argparse.ArgumentParser(description="Inflasi ETL Runner")
    parser.add_argument("--pipeline", "-p", type=str, default="all",
                        choices=["pihps", "kurs", "energy", "fao", "commodity", "news", "bmkg", "global", "all"],
                        help="Pipeline to run")
    parser.add_argument("--date", type=str, help="Tanggal target (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=7, help="Jumlah hari ke belakang")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    if args.date:
        dates = [date.fromisoformat(args.date)]
    else:
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(args.days - 1, -1, -1)]

    # Determine which pipelines to run
    p = args.pipeline
    run_list: list[str] = []
    if p == "all":
        run_list = PIPELINES
    elif p == "global":
        run_list = ["kurs", "energy", "fao", "commodity", "news"]
    else:
        run_list = [p]

    print(f"\n{'='*60}")
    print(f"  INFLASI ETL RUNNER")
    print(f"  Database : {DATABASE_URL.split('@')[-1]}")
    print(f"  Pipelines: {', '.join(run_list)}")
    print(f"  Periode  : {dates[0]} — {dates[-1]} ({len(dates)} hari)")
    print(f"{'='*60}")

    engine = create_async_engine(DATABASE_URL, echo=args.verbose)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    results: dict[str, int] = {}
    async with session_factory() as db:
        for pipeline_name in run_list:
            try:
                if pipeline_name == "pihps":
                    results["pihps"] = await run_pihps(db, dates, args.verbose)
                elif pipeline_name == "kurs":
                    results["kurs"] = await run_kurs(db, args.days, args.verbose)
                elif pipeline_name == "energy":
                    results["energy"] = await run_energy(db, max(args.days, 90), args.verbose)
                elif pipeline_name == "fao":
                    results["fao"] = await run_fao(db, args.verbose)
                elif pipeline_name == "commodity":
                    results["commodity"] = await run_commodity(db, args.verbose)
                elif pipeline_name == "news":
                    results["news"] = await run_news(db, min(args.days, 7), args.verbose)
                elif pipeline_name == "bmkg":
                    results["bmkg"] = await run_bmkg(db, dates[-1:], args.verbose)
            except Exception as e:
                print(f"\n  ✗ {pipeline_name} FAILED: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                results[pipeline_name] = 0

    await engine.dispose()

    print(f"\n{'='*60}")
    print(f"  HASIL:")
    for name, count in results.items():
        status = "✓" if count > 0 else "✗"
        print(f"    {status} {name}: {count} records")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
