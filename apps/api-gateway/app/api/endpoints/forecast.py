import csv
import io
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.forecast_engine import MODEL_VERSION, ForecastEngine

router = APIRouter()


async def _resolve_ids(db: AsyncSession, commodity_code: str, region_code: str):
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
    commodity: str = Query(..., description="Kode komoditas, e.g. bawang_merah"),
    region: str = Query("00", description="Kode wilayah"),
    horizon: int = Query(14, description="Horizon prediksi (7, 14, atau 30)"),
    db: AsyncSession = Depends(get_db),
):
    """Forecast values for a commodity-region pair, joined with ground-truth targets.

    Response includes `actual` price + `target_h7/h14/h30` (supervised labels)
    pulled from `feature_store_daily`, plus accuracy metrics computed over the
    last 30 days.
    """
    cid, rid = await _resolve_ids(db, commodity, region)
    if not cid or not rid:
        return {
            "data": [], "commodity": commodity, "region": region,
            "modelVersion": MODEL_VERSION, "metrics": {},
        }

    engine = ForecastEngine(db)
    data = await engine.get_forecast(cid, rid, horizon)
    metrics = await engine.get_metrics(cid, rid)
    return {
        "data": data,
        "commodity": commodity,
        "region": region,
        "modelVersion": MODEL_VERSION,
        "metrics": metrics,
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
    count = await engine.forecast_all(horizon)
    return {"status": "ok", "forecasted": count}


@router.get("/feature-row")
async def get_feature_row(
    commodity: str = Query(..., description="Kode komoditas"),
    region: str = Query(..., description="Kode wilayah"),
    date: str = Query(..., description="Tanggal YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """Return a single `feature_store_daily` row — for ML inspector / debugging."""
    row = (await db.execute(
        text("""
            SELECT *
            FROM feature_store_daily
            WHERE commodity_id = :commodity
              AND region_id = :region
              AND date = :date
            LIMIT 1
        """),
        {"commodity": commodity, "region": region, "date": date},
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="feature row not found")
    return dict(row)


@router.get("/dataset/export")
async def export_dataset(
    split: str | None = Query(None, description="train | val | test (omit = all)"),
    commodity: str | None = Query(None),
    region: str | None = Query(None),
    start: str | None = Query(None, description="YYYY-MM-DD"),
    end: str | None = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """Stream `feature_store_daily` as CSV (compatible with unified_ready_dataset)."""
    where = ["1=1"]
    params: dict = {}
    if split:
        where.append("split = :split"); params["split"] = split
    if commodity:
        where.append("commodity_id = :commodity"); params["commodity"] = commodity
    if region:
        where.append("region_id = :region"); params["region"] = region
    if start:
        where.append("date >= :start"); params["start"] = start
    if end:
        where.append("date <= :end"); params["end"] = end

    sql = f"SELECT * FROM feature_store_daily WHERE {' AND '.join(where)} ORDER BY date, commodity_id, region_id"

    async def stream() -> AsyncGenerator[bytes, None]:
        result = await db.stream(text(sql), params)
        first = True
        async for partition in result.partitions(500):
            buf = io.StringIO()
            writer = csv.writer(buf)
            for row in partition:
                row_map = row._mapping
                if first:
                    writer.writerow(list(row_map.keys()))
                    first = False
                writer.writerow(list(row_map.values()))
            yield buf.getvalue().encode("utf-8")

    filename = f"feature_store_{split or 'all'}.csv"
    return StreamingResponse(
        stream(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
