from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.driver_analyzer import DriverAnalyzer

router = APIRouter()


@router.get("/analysis")
async def get_driver_analysis(
    commodity: str = Query(..., description="Kode komoditas, e.g. CABAI_RAWIT"),
    region: str = Query("00", description="Kode wilayah"),
    tanggal: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Analyze price drivers for a commodity-region pair."""
    # Resolve codes to IDs
    result = await db.execute(
        text("""
            SELECT
                (SELECT id FROM dim_commodity WHERE kode_komoditas = :cc LIMIT 1) AS cid,
                (SELECT id FROM dim_region WHERE kode_wilayah = :rc LIMIT 1) AS rid
        """),
        {"cc": commodity, "rc": region},
    )
    row = result.first()
    if not row or not row.cid or not row.rid:
        return {
            "commodity": commodity,
            "tanggal": str(tanggal or date.today()),
            "drivers": [],
        }

    analyzer = DriverAnalyzer(db)
    return await analyzer.analyze(row.cid, row.rid, tanggal)
