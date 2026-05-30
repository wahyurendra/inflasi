from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.core.ids import new_id
from app.models.tables import PriceReport, DimCommodity, DimRegion, FactPriceDaily

router = APIRouter()


class CreateReportRequest(BaseModel):
    commodityId: int
    regionId: int
    harga: float
    satuan: str
    namaPasar: str
    kota: str | None = None
    kecamatan: str | None = None
    tanggal: str
    catatan: str | None = None


class UpdateReportRequest(BaseModel):
    status: str
    rejectionNote: str | None = None


class ValidateRequest(BaseModel):
    commodityId: int
    regionId: int
    harga: float


class DetectDuplicateRequest(BaseModel):
    userId: str
    commodityId: int
    regionId: int
    tanggal: str


@router.get("/")
async def list_reports(
    status: str = Query(None),
    commodityId: int = Query(None),
    regionId: int = Query(None),
    page: int = Query(1),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db),
):
    q = select(PriceReport)
    count_q = select(func.count(PriceReport.id))

    if status:
        q = q.where(PriceReport.status == status)
        count_q = count_q.where(PriceReport.status == status)
    if commodityId:
        q = q.where(PriceReport.commodity_id == commodityId)
        count_q = count_q.where(PriceReport.commodity_id == commodityId)
    if regionId:
        q = q.where(PriceReport.region_id == regionId)
        count_q = count_q.where(PriceReport.region_id == regionId)

    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(PriceReport.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "data": [_report_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "totalPages": (total + limit - 1) // limit,
    }


@router.post("/")
async def create_report(
    body: CreateReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    report = PriceReport(
        id=new_id(),
        user_id=current_user["id"],
        commodity_id=body.commodityId,
        region_id=body.regionId,
        harga=body.harga,
        satuan=body.satuan,
        nama_pasar=body.namaPasar,
        kota=body.kota,
        kecamatan=body.kecamatan,
        tanggal=date.fromisoformat(body.tanggal),
        catatan=body.catatan,
        status="PENDING",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Enqueue for async validation (best-effort — the report exists regardless of Redis).
    try:
        from app.core.redis import get_redis
        await get_redis().xadd("stream:price_reports", {"report_id": report.id})
    except Exception:
        pass

    return {"data": _report_to_dict(report)}


@router.get("/my")
async def my_reports(
    page: int = Query(1),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = select(PriceReport).where(PriceReport.user_id == current_user["id"])
    count_q = select(func.count(PriceReport.id)).where(PriceReport.user_id == current_user["id"])

    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(PriceReport.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "data": [_report_to_dict(r) for r in rows],
        "total": total,
        "page": page,
    }


@router.get("/stats")
async def report_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(PriceReport.id)))).scalar() or 0
    approved = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.status == "APPROVED"))).scalar() or 0
    pending = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.status == "PENDING"))).scalar() or 0
    flagged = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.status == "FLAGGED"))).scalar() or 0
    rejected = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.status == "REJECTED"))).scalar() or 0

    return {
        "total": total,
        "approved": approved,
        "pending": pending,
        "flagged": flagged,
        "rejected": rejected,
        "approvalRate": round(approved / total * 100, 1) if total > 0 else 0,
    }


@router.get("/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceReport).where(PriceReport.id == report_id))
    report = result.scalar()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"data": _report_to_dict(report)}


@router.patch("/{report_id}")
async def update_report(
    report_id: str,
    body: UpdateReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(PriceReport).where(PriceReport.id == report_id))
    report = result.scalar()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    from datetime import datetime
    report.status = body.status
    report.reviewed_by = current_user["id"]
    report.reviewed_at = datetime.utcnow()
    if body.rejectionNote:
        report.rejection_note = body.rejectionNote
    await db.commit()
    await db.refresh(report)
    return {"data": _report_to_dict(report)}


@router.post("/validate")
async def validate_report(
    body: ValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate report price against recent median for the same commodity+region."""
    week_ago = date.today() - timedelta(days=7)
    result = await db.execute(
        select(func.percentile_cont(0.5).within_group(FactPriceDaily.harga))
        .where(
            FactPriceDaily.commodity_id == body.commodityId,
            FactPriceDaily.region_id == body.regionId,
            FactPriceDaily.tanggal >= week_ago,
        )
    )
    median = result.scalar()

    if median is None or float(median) == 0:
        return {
            "isValid": True,
            "confidenceScore": 50.0,
            "medianPrice": None,
            "deviation": 0,
            "message": "Tidak ada data harga referensi untuk validasi",
        }

    median_f = float(median)
    deviation = round((body.harga - median_f) / median_f * 100, 2)
    is_valid = abs(deviation) <= 50
    confidence = round(max(0, 100 - abs(deviation)), 2)

    if is_valid:
        message = "Harga dalam rentang wajar"
    elif deviation > 0:
        message = f"Harga {deviation:.1f}% di atas median — terlalu tinggi"
    else:
        message = f"Harga {abs(deviation):.1f}% di bawah median — terlalu rendah"

    return {
        "isValid": is_valid,
        "confidenceScore": confidence,
        "medianPrice": median_f,
        "deviation": deviation,
        "message": message,
    }


@router.post("/detect-duplicate")
async def detect_duplicate(
    body: DetectDuplicateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Check if user already submitted a report for the same commodity+region+date."""
    tanggal = date.fromisoformat(body.tanggal)
    result = await db.execute(
        select(PriceReport).where(
            PriceReport.user_id == body.userId,
            PriceReport.commodity_id == body.commodityId,
            PriceReport.region_id == body.regionId,
            PriceReport.tanggal == tanggal,
        ).limit(1)
    )
    existing = result.scalar()

    return {
        "isDuplicate": existing is not None,
        "existingReportId": existing.id if existing else None,
    }


def _report_to_dict(r: PriceReport) -> dict:
    return {
        "id": r.id,
        "userId": r.user_id,
        "harga": float(r.harga),
        "satuan": r.satuan,
        "namaPasar": r.nama_pasar,
        "tanggal": r.tanggal.isoformat(),
        "status": r.status,
        "catatan": r.catatan,
        "confidenceScore": float(r.confidence_score) if r.confidence_score else None,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
        "commodity": {
            "namaDisplay": r.commodity.nama_display if r.commodity else None,
            "kodeKomoditas": r.commodity.kode_komoditas if r.commodity else None,
        },
        "region": {
            "namaProvinsi": r.region.nama_provinsi if r.region else None,
            "kodeWilayah": r.region.kode_wilayah if r.region else None,
        },
        "user": {
            "name": r.user.name if r.user else None,
        },
        "photos": [
            {"id": p.id, "url": p.url, "filename": p.filename}
            for p in (r.photos or [])
        ],
    }
