from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_id
from app.database import get_db
from app.models.tables import UserPoints, UserBadge, Badge

router = APIRouter()


# ── Request models ───────────────────────────────────────────

class UpsertPointsRequest(BaseModel):
    userId: str
    points: int
    reason: str
    reportId: str | None = None


class UpdateStreakRequest(BaseModel):
    userId: str


class AwardBadgeRequest(BaseModel):
    userId: str
    badgeCode: str


# ── GET endpoints ────────────────────────────────────────────

@router.get("/leaderboard")
async def leaderboard(
    period: str = Query("all"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db),
):
    sort_col = UserPoints.total_points if period == "all" else UserPoints.monthly_points
    q = select(UserPoints).order_by(sort_col.desc()).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()

    data = []
    for i, up in enumerate(rows, 1):
        badge_q = await db.execute(
            select(UserBadge).where(UserBadge.user_id == up.user_id)
        )
        badges = badge_q.scalars().all()

        data.append({
            "rank": i,
            "name": up.user.name if up.user else "Unknown",
            "points": up.total_points if period == "all" else up.monthly_points,
            "reports": up.total_reports,
            "streak": up.current_streak,
            "badges": len(badges),
            "province": up.user.region.nama_provinsi if up.user and up.user.region else None,
        })

    return {"data": data}


@router.get("/user-points")
async def get_user_points(
    user_id: str = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get user's gamification points."""
    result = await db.execute(
        select(UserPoints).where(UserPoints.user_id == user_id)
    )
    up = result.scalar()

    if not up:
        return {"data": {
            "userId": user_id,
            "totalPoints": 0,
            "monthlyPoints": 0,
            "totalReports": 0,
            "approvedReports": 0,
            "currentStreak": 0,
            "longestStreak": 0,
            "lastReportDate": None,
        }}

    return {"data": {
        "userId": up.user_id,
        "totalPoints": up.total_points,
        "monthlyPoints": up.monthly_points,
        "totalReports": up.total_reports,
        "approvedReports": up.approved_reports,
        "currentStreak": up.current_streak,
        "longestStreak": up.longest_streak,
        "lastReportDate": up.last_report_date.isoformat() if up.last_report_date else None,
    }}


@router.get("/user-badges")
async def get_user_badges(
    user_id: str = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get user's earned badges."""
    result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == user_id)
    )
    rows = result.scalars().all()

    return {"data": [
        {
            "badgeId": ub.badge_id,
            "code": ub.badge.code if ub.badge else None,
            "name": ub.badge.name if ub.badge else None,
            "description": ub.badge.description if ub.badge else None,
            "icon": ub.badge.icon if ub.badge else None,
            "category": ub.badge.category if ub.badge else None,
            "earnedAt": ub.earned_at.isoformat() if ub.earned_at else None,
        }
        for ub in rows
    ]}


# ── POST endpoints ───────────────────────────────────────────

@router.post("/upsert-points")
async def upsert_points(
    body: UpsertPointsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add points to user. Creates UserPoints record if not exists."""
    result = await db.execute(
        select(UserPoints).where(UserPoints.user_id == body.userId)
    )
    up = result.scalar()

    if not up:
        up = UserPoints(
            id=new_id(),
            user_id=body.userId,
            total_points=body.points,
            monthly_points=body.points,
            total_reports=1 if body.reason == "report_submitted" else 0,
            approved_reports=1 if body.reason == "report_approved" else 0,
        )
        db.add(up)
    else:
        up.total_points += body.points
        up.monthly_points += body.points
        if body.reason == "report_submitted":
            up.total_reports += 1
        if body.reason == "report_approved":
            up.approved_reports += 1

    await db.commit()
    await db.refresh(up)

    return {"data": {
        "userId": up.user_id,
        "totalPoints": up.total_points,
        "monthlyPoints": up.monthly_points,
    }}


@router.post("/update-streak")
async def update_streak(
    body: UpdateStreakRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update user's daily reporting streak."""
    result = await db.execute(
        select(UserPoints).where(UserPoints.user_id == body.userId)
    )
    up = result.scalar()

    if not up:
        up = UserPoints(
            id=new_id(),
            user_id=body.userId,
            current_streak=1,
            longest_streak=1,
            last_report_date=date.today(),
        )
        db.add(up)
    else:
        today = date.today()
        yesterday = today - timedelta(days=1)

        if up.last_report_date == today:
            pass  # already reported today
        elif up.last_report_date == yesterday:
            up.current_streak += 1
        else:
            up.current_streak = 1

        up.longest_streak = max(up.longest_streak, up.current_streak)
        up.last_report_date = today

    await db.commit()
    await db.refresh(up)

    return {"data": {
        "currentStreak": up.current_streak,
        "longestStreak": up.longest_streak,
    }}


@router.post("/award-badge")
async def award_badge(
    body: AwardBadgeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Award a badge to user. Idempotent — returns existing if already awarded."""
    # Find badge by code
    result = await db.execute(
        select(Badge).where(Badge.code == body.badgeCode)
    )
    badge = result.scalar()
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge '{body.badgeCode}' not found")

    # Check if already awarded
    existing = await db.execute(
        select(UserBadge).where(
            UserBadge.user_id == body.userId,
            UserBadge.badge_id == badge.id,
        )
    )
    ub = existing.scalar()

    if not ub:
        ub = UserBadge(
            id=new_id(),
            user_id=body.userId,
            badge_id=badge.id,
        )
        db.add(ub)
        await db.commit()
        await db.refresh(ub)

    return {"data": {
        "badgeId": badge.id,
        "code": badge.code,
        "name": badge.name,
        "earnedAt": ub.earned_at.isoformat() if ub.earned_at else None,
    }}
