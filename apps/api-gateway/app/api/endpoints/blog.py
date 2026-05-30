from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.blog_generator import BlogGenerator

router = APIRouter()


@router.get("")
@router.get("/")
async def list_blog_posts(
    limit: int = Query(20, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List published blog posts (newest first)."""
    posts = await BlogGenerator(db).list_published(limit=limit, offset=offset)
    return {"data": posts, "count": len(posts)}


@router.get("/{slug}")
async def get_blog_post(slug: str, db: AsyncSession = Depends(get_db)):
    """Fetch a single published blog post by slug."""
    post = await BlogGenerator(db).get_by_slug(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return post


@router.post("/generate")
async def generate_blog_post(
    tanggal: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger generation for a date (defaults to today)."""
    result = await BlogGenerator(db).generate(tanggal or date.today())
    return {"status": "ok", "post": result}
