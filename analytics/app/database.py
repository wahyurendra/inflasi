import ssl

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_url = settings.database_url
_kwargs = {"echo": False, "pool_size": 5, "max_overflow": 10, "pool_recycle": 300}

if "supabase" in _url:
    ssl_ctx = ssl.create_default_context()
    _kwargs["connect_args"] = {"ssl": ssl_ctx}
    _url = _url.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")

engine = create_async_engine(_url, **_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
