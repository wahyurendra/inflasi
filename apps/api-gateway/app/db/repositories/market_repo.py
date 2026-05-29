"""Repository for `dim_market`.

CRUD only — the fuzzy lookup that maps a free-text `nama_pasar` to a market_id
lives in `app/etl/pipelines/market_normalizer.py` to keep the repo dumb.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import DimMarket


class MarketRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, market_id: int) -> DimMarket | None:
        return (await self.db.execute(
            select(DimMarket).where(DimMarket.id == market_id)
        )).scalar_one_or_none()

    async def list_by_region(
        self, region_id: int, *, active_only: bool = True,
    ) -> list[DimMarket]:
        stmt = select(DimMarket).where(DimMarket.region_id == region_id)
        if active_only:
            stmt = stmt.where(DimMarket.is_active.is_(True))
        stmt = stmt.order_by(DimMarket.nama_pasar)
        return list((await self.db.execute(stmt)).scalars().all())

    async def find_by_region_name(
        self, *, region_id: int, nama_pasar: str,
    ) -> DimMarket | None:
        stmt = select(DimMarket).where(
            DimMarket.region_id == region_id,
            DimMarket.nama_pasar.ilike(nama_pasar),
        ).limit(1)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def upsert(
        self,
        *,
        region_id: int,
        nama_pasar: str,
        kode_pasar: str | None = None,
        tipe_pasar: str | None = None,
        alamat: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        is_active: bool = True,
    ) -> DimMarket:
        existing = await self.find_by_region_name(
            region_id=region_id, nama_pasar=nama_pasar,
        )
        if existing:
            if kode_pasar is not None:
                existing.kode_pasar = kode_pasar
            if tipe_pasar is not None:
                existing.tipe_pasar = tipe_pasar
            if alamat is not None:
                existing.alamat = alamat
            if latitude is not None:
                existing.latitude = Decimal(str(latitude))
            if longitude is not None:
                existing.longitude = Decimal(str(longitude))
            existing.is_active = is_active
            await self.db.flush()
            return existing

        row = DimMarket(
            region_id=region_id,
            nama_pasar=nama_pasar,
            kode_pasar=kode_pasar,
            tipe_pasar=tipe_pasar,
            alamat=alamat,
            latitude=Decimal(str(latitude)) if latitude is not None else None,
            longitude=Decimal(str(longitude)) if longitude is not None else None,
            is_active=is_active,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def update(
        self, market_id: int, fields: dict[str, Any],
    ) -> DimMarket | None:
        row = await self.get(market_id)
        if row is None:
            return None
        for k, v in fields.items():
            if not hasattr(row, k):
                continue
            if k in {"latitude", "longitude"} and v is not None:
                v = Decimal(str(v))
            setattr(row, k, v)
        await self.db.flush()
        return row
