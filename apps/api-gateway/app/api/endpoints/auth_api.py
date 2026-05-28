"""Auth endpoints. Under Firebase auth the api-gateway no longer issues tokens or
checks passwords — it only resolves the current user from a verified Firebase ID
token (see app/api/deps.py). Login / register / password changes happen client-side
via the Firebase SDK.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user

router = APIRouter()


@router.get("/me")
async def me(current: dict = Depends(get_current_user)) -> dict:
    """Return the current user's app profile (role/region live in Postgres, not the token).

    The web/Android client calls this right after Firebase sign-in to learn the
    user's role; the user row is created on first call if it doesn't exist yet.
    """
    return {
        "id": current["id"],
        "name": current.get("name"),
        "email": current.get("email"),
        "image": current.get("image"),
        "role": current["role"],
        "regionId": current.get("region_id"),
    }
