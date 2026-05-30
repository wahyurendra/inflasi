from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import FactInflationMonthly

router = APIRouter()


# Seed scripts (backfill_bps_static.py) insert headline rows with kelompok='umum'
# rather than NULL. Match either form so the endpoint works regardless of which
# seeder populated the table.
#
# Postgres treats NULL != NULL in unique constraints, so the seed's
# (periode, region_id, kelompok, commodity_id) UPSERT does not actually merge
# rows where commodity_id IS NULL — each BPS column (mtm/ytd/yoy/ihk) lands
# in its own row. We aggregate via MAX() per period so the latest non-null
# value for each field wins, recovering the intended denormalised shape.
_HEADLINE_FILTER = (
    or_(FactInflationMonthly.kelompok == None, FactInflationMonthly.kelompok == "umum"),
    FactInflationMonthly.commodity_id == None,
)


def _aggregated_select():
    """Select periode + max-aggregated metrics per (periode) for headline rows."""
    return (
        select(
            FactInflationMonthly.periode.label("periode"),
            func.max(FactInflationMonthly.inflasi_mtm).label("mtm"),
            func.max(FactInflationMonthly.inflasi_ytd).label("ytd"),
            func.max(FactInflationMonthly.inflasi_yoy).label("yoy"),
            func.max(FactInflationMonthly.ihk).label("ihk"),
        )
        .where(*_HEADLINE_FILTER)
        .group_by(FactInflationMonthly.periode)
    )


@router.get("/headline")
async def headline_inflation(db: AsyncSession = Depends(get_db)):
    q = _aggregated_select().order_by(FactInflationMonthly.periode.desc()).limit(1)
    result = await db.execute(q)
    row = result.first()

    if not row:
        return {"inflasi": None}

    return {
        "inflasi": {
            "mtm": float(row.mtm) if row.mtm is not None else None,
            "ytd": float(row.ytd) if row.ytd is not None else None,
            "yoy": float(row.yoy) if row.yoy is not None else None,
            "ihk": float(row.ihk) if row.ihk is not None else None,
            "periode": row.periode.isoformat(),
        }
    }


@router.get("/series")
async def inflation_series(
    months: int = Query(12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
):
    """Last N months of national headline inflation (oldest → newest)."""
    q = (
        _aggregated_select()
        .order_by(FactInflationMonthly.periode.desc())
        .limit(months)
    )
    result = await db.execute(q)
    rows = list(result.all())
    rows.reverse()  # oldest first for chart

    return {
        "data": [
            {
                "periode": row.periode.isoformat(),
                "mtm": float(row.mtm) if row.mtm is not None else None,
                "ytd": float(row.ytd) if row.ytd is not None else None,
                "yoy": float(row.yoy) if row.yoy is not None else None,
                "ihk": float(row.ihk) if row.ihk is not None else None,
            }
            for row in rows
        ]
    }
