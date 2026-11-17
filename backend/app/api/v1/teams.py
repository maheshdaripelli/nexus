from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == org_id,
            Membership.user_id == user_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return membership


async def require_team_admin(db: AsyncSession, org_id: UUID, user_id: UUID):
    membership = await require_membership(db, org_id, user_id)
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only organization admins can manage teams")
    return membership


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    organization_id: UUID,
    payload: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_team_admin(db, organization_id, current_user.id)
    team = Team(
        organization_id=organization_id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
    )
    db.add(team)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A team with this name already exists") from exc
    await record_audit_event(
        db, action="team.created", resource_type="team",
        organization_id=organization_id, actor_user_id=current_user.id,
        resource_id=team.id, details={"name": team.name},
    )
    await db.commit()
    await db.refresh(team)
    return team


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_membership(db, organization_id, current_user.id)
    result = await db.scalars(
        select(Team)
        .where(Team.organization_id == organization_id)
        .order_by(Team.created_at.desc())
    )
    return list(result.all())


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    organization_id: UUID,
    team_id: UUID,
    payload: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_team_admin(db, organization_id, current_user.id)
    team = await db.scalar(
        select(Team).where(Team.id == team_id, Team.organization_id == organization_id)
    )
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    team.name = payload.name.strip()
    team.description = payload.description.strip() if payload.description else None
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A team with this name already exists") from exc
    await record_audit_event(
        db, action="team.updated", resource_type="team",
        organization_id=organization_id, actor_user_id=current_user.id,
        resource_id=team.id, details={"name": team.name},
    )
    await db.commit()
    await db.refresh(team)
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    organization_id: UUID,
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_team_admin(db, organization_id, current_user.id)
    team = await db.scalar(
        select(Team).where(Team.id == team_id, Team.organization_id == organization_id)
    )
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    await record_audit_event(
        db, action="team.deleted", resource_type="team",
        organization_id=organization_id, actor_user_id=current_user.id,
        resource_id=team.id, details={"name": team.name},
    )
    await db.delete(team)
    await db.commit()
