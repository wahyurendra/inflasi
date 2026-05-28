from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.tables import User, PriceReport

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    name: str


class AdminUpdateUserRequest(BaseModel):
    role: str | None = None
    isActive: bool | None = None


# ── User profile ─────────────────────────────────────────────

# NOTE: /me/* must be declared before /{user_id}/* so the literal wins routing.

@router.get("/me/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    return {
        "data": {
            "id": current_user["id"],
            "name": current_user.get("name"),
            "email": current_user.get("email"),
            "role": current_user["role"],
            "regionId": current_user.get("region_id"),
            "image": current_user.get("image"),
        }
    }


@router.patch("/me/profile")
async def update_my_profile(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = body.name
    await db.commit()
    return {"data": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}


@router.get("/{user_id}/profile")
async def get_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["id"] != user_id and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "regionId": user.region_id,
            "image": user.image,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
        }
    }


@router.patch("/{user_id}/profile")
async def update_profile(
    user_id: str,
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["id"] != user_id and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = body.name
    await db.commit()

    return {
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }
    }


# ── Admin endpoints ──────────────────────────────────────────

@router.get("/admin/list")
async def admin_list_users(
    role: str = Query(None),
    page: int = Query(1),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    q = select(User)
    if role:
        q = q.where(User.role == role)
    q = q.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)

    result = await db.execute(q)
    users = result.scalars().all()

    count_q = select(func.count(User.id))
    if role:
        count_q = count_q.where(User.role == role)
    total = (await db.execute(count_q)).scalar() or 0

    return {
        "data": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "isActive": u.is_active,
                "createdAt": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "totalPages": (total + limit - 1) // limit,
    }


@router.patch("/admin/{user_id}")
async def admin_update_user(
    user_id: str,
    body: AdminUpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        user.role = body.role
    if body.isActive is not None:
        user.is_active = body.isActive
    await db.commit()

    return {"data": {"id": user.id, "role": user.role, "isActive": user.is_active}}


@router.get("/admin/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    from datetime import date, timedelta
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_start = today.replace(day=1)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar() or 0

    total_reports = (await db.execute(select(func.count(PriceReport.id)))).scalar() or 0
    pending = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.status == "PENDING"))).scalar() or 0
    approved = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.status == "APPROVED"))).scalar() or 0
    rejected = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.status == "REJECTED"))).scalar() or 0
    flagged = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.status == "FLAGGED"))).scalar() or 0
    reports_today = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.tanggal == today))).scalar() or 0
    reports_week = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.tanggal >= week_ago))).scalar() or 0
    reports_month = (await db.execute(select(func.count(PriceReport.id)).where(PriceReport.tanggal >= month_start))).scalar() or 0

    # Users by role
    roles_q = await db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    users_by_role = {r: c for r, c in roles_q.all()}

    return {
        "data": {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalReports": total_reports,
            "pendingReports": pending,
            "approvedReports": approved,
            "rejectedReports": rejected,
            "flaggedReports": flagged,
            "reportsToday": reports_today,
            "reportsThisWeek": reports_week,
            "reportsThisMonth": reports_month,
            "usersByRole": {
                "ADMIN": users_by_role.get("ADMIN", 0),
                "GOVERNMENT_ANALYST": users_by_role.get("GOVERNMENT_ANALYST", 0),
                "REGIONAL_OFFICER": users_by_role.get("REGIONAL_OFFICER", 0),
                "REPORTER": users_by_role.get("REPORTER", 0),
            },
        }
    }
