from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.alert_engine import AlertEngine

router = APIRouter()


@router.get("/active")
async def get_active_alerts(
    severity: str | None = Query(None, description="info|warning|critical"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db),
):
    """Get daftar alert aktif."""
    engine = AlertEngine(db)
    return await engine.get_active_alerts(severity, limit)


@router.post("/generate")
async def generate_alerts(
    tanggal: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Jalankan alert engine untuk tanggal tertentu."""
    engine = AlertEngine(db)
    result = await engine.run_daily(tanggal or date.today())
    return {"status": "ok", "alerts_generated": result}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Resolve (tutup) alert tertentu."""
    engine = AlertEngine(db)
    await engine.resolve_alert(alert_id)
    return {"status": "ok"}
