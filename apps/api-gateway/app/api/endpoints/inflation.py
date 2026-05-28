from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import FactInflationMonthly

router = APIRouter()


@router.get("/headline")
async def headline_inflation(db: AsyncSession = Depends(get_db)):
    q = (
        select(FactInflationMonthly)
        .where(FactInflationMonthly.kelompok == None, FactInflationMonthly.commodity_id == None)
        .order_by(FactInflationMonthly.periode.desc())
        .limit(1)
    )
    result = await db.execute(q)
    row = result.scalar()

    if not row:
        return {"inflasi": None}

    return {
        "inflasi": {
            "mtm": float(row.inflasi_mtm) if row.inflasi_mtm else None,
            "ytd": float(row.inflasi_ytd) if row.inflasi_ytd else None,
            "yoy": float(row.inflasi_yoy) if row.inflasi_yoy else None,
            "ihk": float(row.ihk) if row.ihk else None,
            "periode": row.periode.isoformat(),
        }
    }
