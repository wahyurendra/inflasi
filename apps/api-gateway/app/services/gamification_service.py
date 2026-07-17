"""Points/streak/badge awarding for approved crowd-sourced price reports.

Single entry point (`award_for_approved_report`) called by both places a report
can transition to APPROVED: the manual admin PATCH in `app.api.endpoints.reports`
and the auto-validation worker in `app.workers.validation_pipeline`. Idempotent —
guarded by `PriceReport.gamification_awarded_at`, claimed atomically so concurrent
or repeated calls for the same report only award once.

Badge codes/thresholds mirror the canonical seed in `scripts/seed_dimensions.py`.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_id
from app.models.tables import Badge, Notification, PriceReport, UserBadge, UserPoints

BASE_POINTS = 10

# (code, threshold) — checked against UserPoints.approved_reports
MILESTONE_BADGES: tuple[tuple[str, int], ...] = (
    ("first_report", 1),
    ("reporter_10", 10),
    ("reporter_50", 50),
    ("reporter_100", 100),
)

# (code, threshold) — checked against UserPoints.current_streak
STREAK_BADGES: tuple[tuple[str, int], ...] = (
    ("streak_7", 7),
    ("streak_30", 30),
)

# (code, threshold, column) — checked via COUNT(DISTINCT column) over the user's
# APPROVED reports
DIVERSITY_BADGES: tuple[tuple[str, int, object], ...] = (
    ("multi_commodity", 5, PriceReport.commodity_id),
    ("multi_region", 3, PriceReport.region_id),
)


async def _claim_award(db: AsyncSession, report_id: str) -> bool:
    """Atomically claim this report for awarding. False if already claimed."""
    result = await db.execute(
        update(PriceReport)
        .where(PriceReport.id == report_id, PriceReport.gamification_awarded_at.is_(None))
        .values(gamification_awarded_at=func.now())
        .returning(PriceReport.id)
    )
    return result.first() is not None


async def award_badge_if_new(db: AsyncSession, user_id: str, badge_code: str) -> Badge | None:
    """Idempotently award a badge by code. Returns the Badge iff newly awarded
    this call — None if the code isn't seeded, or the user already has it."""
    badge = (await db.execute(select(Badge).where(Badge.code == badge_code))).scalar()
    if badge is None:
        return None

    existing = (
        await db.execute(
            select(UserBadge.id).where(
                UserBadge.user_id == user_id, UserBadge.badge_id == badge.id
            )
        )
    ).scalar()
    if existing is not None:
        return None

    db.add(UserBadge(id=new_id(), user_id=user_id, badge_id=badge.id))
    return badge


async def _check_badges(db: AsyncSession, user_id: str, up: UserPoints) -> list[Badge]:
    newly: list[Badge] = []

    for code, threshold in MILESTONE_BADGES:
        if up.approved_reports >= threshold:
            badge = await award_badge_if_new(db, user_id, code)
            if badge:
                newly.append(badge)

    for code, threshold in STREAK_BADGES:
        if up.current_streak >= threshold:
            badge = await award_badge_if_new(db, user_id, code)
            if badge:
                newly.append(badge)

    for code, threshold, column in DIVERSITY_BADGES:
        count = (
            await db.execute(
                select(func.count(func.distinct(column))).where(
                    PriceReport.user_id == user_id, PriceReport.status == "APPROVED"
                )
            )
        ).scalar() or 0
        if count >= threshold:
            badge = await award_badge_if_new(db, user_id, code)
            if badge:
                newly.append(badge)

    return newly


async def award_for_approved_report(db: AsyncSession, report: PriceReport) -> dict | None:
    """Award points/streak/badges for a report that just became APPROVED and
    write a `report_approved` notification carrying everything the frontend
    popup needs to render. Does not commit — the caller's existing commit
    (status flip + this) is one transaction.

    Returns None if this report was already awarded (double-approval, retry,
    or redelivery) — no side effects in that case.
    """
    if not await _claim_award(db, report.id):
        return None

    up = (
        await db.execute(select(UserPoints).where(UserPoints.user_id == report.user_id))
    ).scalar()
    if up is None:
        up = UserPoints(id=new_id(), user_id=report.user_id)
        db.add(up)
        await db.flush()

    points = BASE_POINTS
    up.total_points += points
    up.monthly_points += points
    up.approved_reports += 1

    today = date.today()
    if up.last_report_date == today:
        pass  # already reported (and streaked) today
    elif up.last_report_date == today - timedelta(days=1):
        up.current_streak += 1
    else:
        up.current_streak = 1
    up.longest_streak = max(up.longest_streak, up.current_streak)
    up.last_report_date = today

    await db.flush()  # badge threshold checks below need up.* committed to the session

    new_badges = await _check_badges(db, report.user_id, up)

    payload = {
        "reportId": report.id,
        "pointsEarned": points,
        "totalPoints": up.total_points,
        "currentStreak": up.current_streak,
        "newBadges": [
            {"code": b.code, "name": b.name, "icon": b.icon, "description": b.description}
            for b in new_badges
        ],
    }

    message = f"Anda mendapat {points} poin"
    if new_badges:
        message += f" dan {len(new_badges)} badge baru"
    message += "!"

    db.add(
        Notification(
            id=new_id(),
            user_id=report.user_id,
            type="report_approved",
            title="Laporan disetujui!",
            message=message,
            data=payload,
        )
    )

    return payload
