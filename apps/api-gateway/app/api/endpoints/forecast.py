from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.forecast_engine import ForecastEngine

router = APIRouter()


async def _resolve_ids(db: AsyncSession, commodity_code: str, region_code: str):
    """Resolve kode_komoditas and kode_wilayah to integer IDs."""
    result = await db.execute(
        text("""
            SELECT
                (SELECT id FROM dim_commodity WHERE kode_komoditas = :cc LIMIT 1) AS cid,
                (SELECT id FROM dim_region WHERE kode_wilayah = :rc LIMIT 1) AS rid
        """),
        {"cc": commodity_code, "rc": region_code},
    )
    row = result.first()
    if row and row.cid and row.rid:
        return row.cid, row.rid
    return None, None


@router.get("/prices")
async def get_forecast_prices(
    commodity: str = Query(..., description="Kode komoditas, e.g. CABAI_RAWIT"),
    region: str = Query("00", description="Kode wilayah"),
    horizon: int = Query(14, description="Horizon prediksi (7 atau 14)"),
    db: AsyncSession = Depends(get_db),
):
    """Get stored forecast prices for a commodity-region pair."""
    cid, rid = await _resolve_ids(db, commodity, region)
    if not cid or not rid:
        return {"data": [], "commodity": commodity, "region": region, "modelVersion": "prophet-v1"}

    engine = ForecastEngine(db)
    data = await engine.get_forecast(cid, rid, horizon)
    return {
        "data": data,
        "commodity": commodity,
        "region": region,
        "modelVersion": "prophet-v1",
    }


@router.post("/run")
async def run_forecast(
    commodity_code: str = Query(None, description="Kode komoditas (kosong = semua)"),
    horizon: int = Query(14),
    db: AsyncSession = Depends(get_db),
):
    """Trigger forecast computation for one or all commodities."""
    engine = ForecastEngine(db)

    if commodity_code:
        cid, rid = await _resolve_ids(db, commodity_code, "00")
        if not cid or not rid:
            return {"status": "error", "message": f"Commodity {commodity_code} not found"}
        result = await engine.forecast_commodity(cid, rid, horizon)
        return {"status": "ok", "forecasted": 1, "points": len(result)}
    else:
        count = await engine.forecast_all(horizon)
        return {"status": "ok", "forecasted": count}
