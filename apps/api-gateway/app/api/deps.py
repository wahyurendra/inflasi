"""FastAPI auth dependencies — Firebase ID-token verification.

The web/Android client sends `Authorization: Bearer <Firebase ID token>`; we verify
it (app/core/firebase.py), then resolve the matching `User` row (by firebase_uid,
linking an existing email account on first sign-in, or creating a REPORTER). App-
specific authorization (role, region) lives in Postgres, not in the token.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.firebase import verify_id_token
from app.database import get_db
from app.models.tables import User

_bearer_scheme = HTTPBearer(auto_error=False)


async def _user_from_token(
    credentials: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User | None:
    if not credentials:
        return None
    try:
        decoded = verify_id_token(credentials.credentials)
    except Exception:
        return None

    uid = decoded.get("uid") or decoded.get("user_id")
    if not uid:
        return None
    email = decoded.get("email")

    user = (await db.execute(select(User).where(User.firebase_uid == uid))).scalar()

    # First sign-in: link a pre-existing account by email, else create one.
    if user is None and email:
        user = (await db.execute(select(User).where(User.email == email))).scalar()
        if user is not None:
            user.firebase_uid = uid

    if user is None:
        import cuid2
        user = User(
            id=cuid2.cuid_wrapper(),
            firebase_uid=uid,
            email=email or f"{uid}@firebase.local",
            name=decoded.get("name"),
            image=decoded.get("picture"),
            role="REPORTER",
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user


def _to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "firebase_uid": user.firebase_uid,
        "email": user.email,
        "name": user.name,
        "image": user.image,
        "role": user.role,
        "region_id": user.region_id,
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Require a valid Firebase ID token; returns the resolved user."""
    user = await _user_from_token(credentials, db)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Tidak terautentikasi")
    return _to_dict(user)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict | None:
    """Optional auth — returns None when no/invalid token is present."""
    user = await _user_from_token(credentials, db)
    return _to_dict(user) if user and user.is_active else None
