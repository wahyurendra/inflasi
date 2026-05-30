from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.core.ids import new_id
from app.models.tables import Notification

router = APIRouter()


class CreateNotificationRequest(BaseModel):
    userId: str
    type: str
    title: str
    message: str
    data: dict | None = None


class MarkReadRequest(BaseModel):
    ids: list[str] | None = None
    all: bool = False


@router.get("/")
async def list_notifications(
    page: int = Query(1),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = select(Notification).where(Notification.user_id == current_user["id"])
    count_q = select(func.count(Notification.id)).where(Notification.user_id == current_user["id"])

    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "data": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "data": n.data,
                "isRead": n.is_read,
                "createdAt": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ],
        "total": total,
        "page": page,
    }


@router.get("/count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == current_user["id"], Notification.is_read == False)
    )
    return {"count": result.scalar() or 0}


@router.post("/")
async def create_notification(
    body: CreateNotificationRequest,
    db: AsyncSession = Depends(get_db),
):
    notif = Notification(
        id=new_id(),
        user_id=body.userId,
        type=body.type,
        title=body.title,
        message=body.message,
        data=body.data,
    )
    db.add(notif)
    await db.commit()
    return {"success": True}


@router.patch("/mark-read")
async def mark_read(
    body: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if body.all:
        await db.execute(
            update(Notification)
            .where(Notification.user_id == current_user["id"], Notification.is_read == False)
            .values(is_read=True)
        )
    elif body.ids:
        await db.execute(
            update(Notification)
            .where(Notification.id.in_(body.ids), Notification.user_id == current_user["id"])
            .values(is_read=True)
        )
    await db.commit()
    return {"success": True}
