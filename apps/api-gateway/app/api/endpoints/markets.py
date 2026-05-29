"""Markets endpoint — CRUD `dim_market` plus a quick fuzzy lookup helper.

Mounted at `/api/markets`. Read endpoints are public (the dashboard renders
market selectors); write endpoints require ADMIN/GOVERNMENT_ANALYST.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.db.repositories.market_repo import MarketRepo
from app.etl.pipelines.market_normalizer import MarketNormalizer

router = APIRouter()


class MarketRow(BaseModel):
    id: int
    region_id: int
    kode_pasar: str | None = None
    nama_pasar: str
    tipe_pasar: str | None = None
    alamat: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool


class MarketUpsertRequest(BaseModel):
    region_id: int
    nama_pasar: str = Field(..., min_length=2, max_length=200)
    kode_pasar: str | None = None
    tipe_pasar: str | None = None
    alamat: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool = True


class MarketUpdateRequest(BaseModel):
    nama_pasar: str | None = Field(None, min_length=2, max_length=200)
    kode_pasar: str | None = None
    tipe_pasar: str | None = None
    alamat: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool | None = None


def _require_admin(user: dict) -> None:
    if user.get("role") not in {"ADMIN", "GOVERNMENT_ANALYST"}:
        raise HTTPException(status_code=403, detail="admin role required")


def _to_schema(row) -> MarketRow:
    return MarketRow(
        id=row.id,
        region_id=row.region_id,
        kode_pasar=row.kode_pasar,
        nama_pasar=row.nama_pasar,
        tipe_pasar=row.tipe_pasar,
        alamat=row.alamat,
        latitude=float(row.latitude) if row.latitude is not None else None,
        longitude=float(row.longitude) if row.longitude is not None else None,
        is_active=row.is_active,
    )


@router.get("", response_model=list[MarketRow])
async def list_markets(
    region_id: int = Query(..., description="dim_region.id"),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> list[MarketRow]:
    rows = await MarketRepo(db).list_by_region(region_id, active_only=active_only)
    return [_to_schema(r) for r in rows]


@router.get("/resolve")
async def resolve_market(
    region_id: int = Query(...),
    nama_pasar: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Cheap probe used by the report-create form to pre-fill `market_id`.

    Returns the match (with score + method) or `{"match": null}` on miss.
    Never auto-creates — validation pipeline owns that decision.
    """
    match = await MarketNormalizer(db).resolve(
        region_id=region_id, nama_pasar=nama_pasar, auto_create=False,
    )
    if match is None:
        return {"match": None}
    return {
        "match": {
            "market_id": match.market_id,
            "nama_pasar": match.nama_pasar,
            "score": match.score,
            "method": match.method,
        },
    }


@router.post("", response_model=MarketRow)
async def create_or_update_market(
    body: MarketUpsertRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> MarketRow:
    _require_admin(user)
    row = await MarketRepo(db).upsert(
        region_id=body.region_id,
        nama_pasar=body.nama_pasar,
        kode_pasar=body.kode_pasar,
        tipe_pasar=body.tipe_pasar,
        alamat=body.alamat,
        latitude=body.latitude,
        longitude=body.longitude,
        is_active=body.is_active,
    )
    await db.commit()
    return _to_schema(row)


@router.patch("/{market_id}", response_model=MarketRow)
async def patch_market(
    market_id: int,
    body: MarketUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> MarketRow:
    _require_admin(user)
    fields = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    row = await MarketRepo(db).update(market_id, fields)
    if row is None:
        raise HTTPException(status_code=404, detail="market not found")
    await db.commit()
    return _to_schema(row)
