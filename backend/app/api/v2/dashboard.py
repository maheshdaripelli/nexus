from uuid import UUID
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.membership import Membership
from app.models.team import Team
from app.models.user import User
from app.services.authorization import require_permission

router = APIRouter(prefix="/organizations/{organization_id}/dashboard", tags=["V2 dashboard"])

@router.get("/stats")
async def organization_stats(organization_id: UUID, request: Request, response: Response,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Never cache or bypass authorization.
    await require_permission(db, organization_id, user.id, "members.read")
    await require_permission(db, organization_id, user.id, "teams.read")
    key = f"nexus:v2:dashboard:stats:{organization_id}"
    cache = request.app.state.cache
    cached, state = await cache.get(key)
    response.headers["X-Cache"] = state
    if cached is not None:
        return cached
    members = await db.scalar(select(func.count(Membership.id)).where(Membership.organization_id == organization_id)) or 0
    teams = await db.scalar(select(func.count(Team.id)).where(Team.organization_id == organization_id)) or 0
    result = {"organization_id": str(organization_id), "member_count": members, "team_count": teams}
    if state == "MISS":
        await cache.set(key, result)
    return result
