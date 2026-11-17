import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.invitation import Invitation
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.services.audit import record_audit_event
from app.services.email import send_invitation_email
from app.api.v1.organizations import make_slug

router = APIRouter(prefix="/platform", tags=["Platform administration"])


class PlatformOrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    owner_email: EmailStr


async def require_platform_admin(db: AsyncSession, user_id):
    if await db.get(PlatformAdmin, user_id) is None:
        raise HTTPException(status_code=403, detail="Platform administrator access required")


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_platform_organization(
    payload: PlatformOrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await require_platform_admin(db, user.id)
    email = str(payload.owner_email).strip().lower()
    name = payload.name.strip()
    org = Organization(name=name, slug=make_slug(name))
    db.add(org)
    await db.flush()

    raw = secrets.token_urlsafe(40)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    invitation = Invitation(
        organization_id=org.id,
        email=email,
        role="owner",
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        invited_by_user_id=user.id,
        expires_at=expires_at,
    )
    db.add(invitation)
    await record_audit_event(
        db,
        action="organization.provisioned",
        resource_type="organization",
        organization_id=org.id,
        actor_user_id=user.id,
        resource_id=org.id,
        details={"name": name, "initial_owner_email": email},
    )
    await db.commit()
    await db.refresh(org)

    invitation_url = (
        f"{settings.FRONTEND_ORIGIN.rstrip('/')}/accept-invitation"
        f"?organization_id={org.id}&token={raw}"
    )
    email_sent = await send_invitation_email(
        to_email=email,
        organization_name=org.name,
        role="owner",
        invitation_url=invitation_url,
        expires_at=expires_at.isoformat(),
    )
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "created_at": org.created_at,
        "owner_email": email,
        "invitation_token": raw,
        "email_sent": email_sent,
        "invitation_expires_at": expires_at,
    }


@router.get("/overview")
async def platform_overview(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    return {
        "organization_count": await db.scalar(select(func.count(Organization.id))) or 0,
        "user_count": await db.scalar(select(func.count(User.id))) or 0,
        "membership_count": await db.scalar(select(func.count(Membership.id))) or 0,
    }


@router.get("/organizations")
async def list_all_organizations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    statement = (
        select(Organization, func.count(Membership.id).label("member_count"))
        .outerjoin(Membership, Membership.organization_id == Organization.id)
        .group_by(Organization.id)
        .order_by(Organization.created_at.desc())
    )
    rows = (await db.execute(statement)).all()
    return [
        {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "created_at": org.created_at,
            "member_count": count,
        }
        for org, count in rows
    ]
