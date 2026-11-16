from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.membership import Membership
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamResponse
from app.services.audit import record_audit_event

router = APIRouter(prefix="/organizations/{organization_id}/teams", tags=["Teams"])

async def require_membership(db: AsyncSession, org_id: UUID, user_id: UUID):
    membership = await db.scalar(select(Membership).where(Membership.organization_id == org_id, Membership.user_id == user_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return membership

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(organization_id: UUID, payload: TeamCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = await require_membership(db, organization_id, current_user.id)
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only organization admins can create teams")
    team = Team(organization_id=organization_id, name=payload.name.strip(), description=payload.description)
    db.add(team)
    await db.flush()
    await record_audit_event(db, action="team.created", resource_type="team", organization_id=organization_id, actor_user_id=current_user.id, resource_id=team.id, details={"name": team.name})
    await db.commit()
    await db.refresh(team)
    return team

@router.get("", response_model=list[TeamResponse])
async def list_teams(organization_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await require_membership(db, organization_id, current_user.id)
    result = await db.scalars(select(Team).where(Team.organization_id == organization_id).order_by(Team.created_at.desc()))
    return list(result.all())
