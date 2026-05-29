import csv
import io
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.forecast import (
    ComponentPrediction,
    DriverImpact,
    ForecastPointSchema,
    PriceForecastRequest,
    PriceForecastResponse,
)
from app.services.forecast_engine import MODEL_VERSION, ForecastEngine
from app.services.prediction_service import PredictionService

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


# ── v2: quantile forecast (POST /forecast/price) ─────────────

@router.post("/price", response_model=PriceForecastResponse)
async def forecast_price_v2(
    body: PriceForecastRequest,
    db: AsyncSession = Depends(get_db),
) -> PriceForecastResponse:
    """Quantile price forecast (p10/p50/p90) with risk + driver explanation.

    Persists to `analytics_forecast` + `forecast_model_components`. Reads the
    active model version from `model_registry` when registered; otherwise stamps
    a deterministic placeholder. Matches the spec in
    docs/INFLASI_ID_Backend_Database_Plan_Updated.md §11.1.
    """
    service = PredictionService(db)
    points = await service.forecast_pair(
        commodity_id=body.commodity_id,
        region_id=body.region_id,
        horizon=body.horizon,
    )
    await db.commit()

    if not points:
        raise HTTPException(
            status_code=404,
            detail="commodity/region not found or no recent data to forecast",
        )

    version = points[0].components[0].get("model_version") if points[0].components else "unknown"
    return PriceForecastResponse(
        commodity_id=body.commodity_id,
        region_id=body.region_id,
        horizon=body.horizon,
        model_version=version or "unknown",
        points=[
            ForecastPointSchema(
                target_date=p.target_date,
                yhat=p.yhat,
                yhat_lower=p.yhat_lower,
                yhat_upper=p.yhat_upper,
                p10=p.p10, p50=p.p50, p90=p.p90,
                risk_level=p.risk_level,
                confidence_score=p.confidence_score,
                top_drivers=[DriverImpact(**d) for d in p.top_drivers],
                model_contribution=p.model_contribution,
                components=[ComponentPrediction(**c) for c in p.components],
            )
            for p in points
        ],
    )


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
