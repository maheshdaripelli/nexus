from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.membership import Membership
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.audit import record_audit_event
from app.services.authorization import require_permission

router = APIRouter(prefix="/organizations/{organization_id}/teams", tags=["Team members"])

async def get_org_membership(db: AsyncSession, organization_id: UUID, user_id: UUID):
    membership = await db.scalar(select(Membership).where(Membership.organization_id == organization_id, Membership.user_id == user_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return membership

async def get_team(db: AsyncSession, organization_id: UUID, team_id: UUID):
    team = await db.scalar(select(Team).where(Team.id == team_id, Team.organization_id == organization_id))
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.get("/{team_id}/members")
async def list_team_members(organization_id: UUID, team_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_permission(db, organization_id, user.id, "teams.read")
    await get_team(db, organization_id, team_id)
    rows = (await db.execute(select(Membership, User, TeamMember).join(TeamMember, TeamMember.membership_id == Membership.id).join(User, User.id == Membership.user_id).where(TeamMember.team_id == team_id).order_by(User.full_name))).all()
    return [{"membership_id": str(m.id), "user_id": str(u.id), "full_name": u.full_name, "email": u.email, "role": m.role, "added_at": tm.added_at} for m,u,tm in rows]

@router.post("/{team_id}/members/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_team_member(organization_id: UUID, team_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_permission(db, organization_id, user.id, "teams.manage")
    await get_team(db, organization_id, team_id)
    target = await db.scalar(select(Membership).where(Membership.organization_id == organization_id, Membership.user_id == user_id))
    if target is None:
        raise HTTPException(status_code=404, detail="User is not a member of this organization")
    existing = await db.scalar(select(TeamMember.id).where(TeamMember.team_id == team_id, TeamMember.membership_id == target.id))
    if existing:
        raise HTTPException(status_code=409, detail="User is already in this team")
    db.add(TeamMember(team_id=team_id, membership_id=target.id))
    await record_audit_event(db, action="team.member_added", resource_type="team", organization_id=organization_id, actor_user_id=user.id, resource_id=team_id, details={"member_user_id": str(user_id)})
    await db.commit()
    return {"message": "Member added to team"}

@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(organization_id: UUID, team_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_permission(db, organization_id, user.id, "teams.manage")
    await get_team(db, organization_id, team_id)
    target = await db.scalar(select(Membership).where(Membership.organization_id == organization_id, Membership.user_id == user_id))
    if target is None:
        raise HTTPException(status_code=404, detail="Organization member not found")
    link = await db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.membership_id == target.id))
    if link is not None:
        await record_audit_event(db, action="team.member_removed", resource_type="team", organization_id=organization_id, actor_user_id=user.id, resource_id=team_id, details={"member_user_id": str(user_id)})
        await db.delete(link)
        await db.commit()
