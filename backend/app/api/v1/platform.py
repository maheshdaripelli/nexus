import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
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

class PlatformOrganizationUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=160)

class PlatformOrganizationStatus(BaseModel):
    is_active: bool

class PlatformAdminCreate(BaseModel):
    email: EmailStr

async def require_platform_admin(db: AsyncSession, user_id: UUID):
    admin = await db.get(PlatformAdmin, user_id)
    if admin is None or admin.access_level != "super_admin":
        raise HTTPException(status_code=403, detail="Platform Super Admin access required")
    return admin

@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_platform_organization(payload: PlatformOrganizationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    email = str(payload.owner_email).strip().lower()
    name = payload.name.strip()
    org = Organization(name=name, slug=make_slug(name), is_active=True)
    db.add(org)
    await db.flush()
    raw = secrets.token_urlsafe(40)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db.add(Invitation(organization_id=org.id, email=email, role="owner", token_hash=hashlib.sha256(raw.encode()).hexdigest(), invited_by_user_id=user.id, expires_at=expires_at))
    await record_audit_event(db, action="organization.provisioned", resource_type="organization", organization_id=org.id, actor_user_id=user.id, resource_id=org.id, details={"name": name, "initial_owner_email": email})
    await db.commit()
    await db.refresh(org)
    invitation_url = f"{settings.FRONTEND_ORIGIN.rstrip('/')}/accept-invitation?organization_id={org.id}&token={raw}"
    email_sent = await send_invitation_email(to_email=email, organization_name=org.name, role="owner", invitation_url=invitation_url, expires_at=expires_at.isoformat())
    return {"id": str(org.id), "name": org.name, "slug": org.slug, "created_at": org.created_at, "is_active": org.is_active, "owner_email": email, "invitation_token": raw, "email_sent": email_sent, "invitation_expires_at": expires_at}

@router.get("/overview")
async def platform_overview(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    return {
        "organization_count": await db.scalar(select(func.count(Organization.id))) or 0,
        "active_organization_count": await db.scalar(select(func.count(Organization.id)).where(Organization.is_active.is_(True))) or 0,
        "suspended_organization_count": await db.scalar(select(func.count(Organization.id)).where(Organization.is_active.is_(False))) or 0,
        "user_count": await db.scalar(select(func.count(User.id))) or 0,
        "membership_count": await db.scalar(select(func.count(Membership.id))) or 0,
        "platform_admin_count": await db.scalar(select(func.count(PlatformAdmin.user_id))) or 0,
    }

@router.get("/organizations")
async def list_all_organizations(search: str | None = Query(default=None, max_length=160), status_filter: str = Query(default="all", alias="status"), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    if status_filter not in {"all", "active", "suspended"}:
        raise HTTPException(status_code=400, detail="Status must be all, active, or suspended")
    stmt = select(Organization, func.count(Membership.id).label("member_count")).outerjoin(Membership, Membership.organization_id == Organization.id).group_by(Organization.id)
    if status_filter == "active": stmt = stmt.where(Organization.is_active.is_(True))
    if status_filter == "suspended": stmt = stmt.where(Organization.is_active.is_(False))
    if search and search.strip(): stmt = stmt.where(Organization.name.ilike(f"%{search.strip()}%"))
    rows = (await db.execute(stmt.order_by(Organization.created_at.desc()))).all()
    result = []
    for org, count in rows:
        owner = await db.scalar(select(User).join(Membership, Membership.user_id == User.id).where(Membership.organization_id == org.id, Membership.role == "owner").order_by(Membership.created_at).limit(1))
        pending_owner = await db.scalar(select(Invitation.email).where(Invitation.organization_id == org.id, Invitation.role == "owner", Invitation.status == "pending").order_by(Invitation.created_at.desc()).limit(1))
        result.append({"id": str(org.id), "name": org.name, "slug": org.slug, "created_at": org.created_at, "is_active": org.is_active, "member_count": count, "owner_name": owner.full_name if owner else None, "owner_email": owner.email if owner else pending_owner})
    return result

@router.get("/organizations/{organization_id}")
async def get_platform_organization(organization_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    org = await db.get(Organization, organization_id)
    if org is None: raise HTTPException(status_code=404, detail="Organization not found")
    members = (await db.execute(select(Membership, User).join(User, User.id == Membership.user_id).where(Membership.organization_id == org.id).order_by(Membership.created_at))).all()
    invitations = (await db.scalars(select(Invitation).where(Invitation.organization_id == org.id).order_by(Invitation.created_at.desc()).limit(50))).all()
    return {"id": str(org.id), "name": org.name, "slug": org.slug, "created_at": org.created_at, "is_active": org.is_active, "members": [{"id": str(m.id), "user_id": str(u.id), "full_name": u.full_name, "email": u.email, "role": m.role, "custom_role_id": str(m.custom_role_id) if m.custom_role_id else None} for m,u in members], "invitations": [{"id": str(i.id), "email": i.email, "role": i.role, "status": i.status, "expires_at": i.expires_at, "created_at": i.created_at} for i in invitations]}

@router.patch("/organizations/{organization_id}")
async def update_platform_organization(organization_id: UUID, payload: PlatformOrganizationUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    org = await db.get(Organization, organization_id)
    if org is None: raise HTTPException(status_code=404, detail="Organization not found")
    name = payload.name.strip()
    if len(name) < 2: raise HTTPException(status_code=422, detail="Organization name must contain at least 2 characters")
    old_name = org.name
    org.name = name
    await record_audit_event(db, action="platform.organization_updated", resource_type="organization", organization_id=org.id, actor_user_id=user.id, resource_id=org.id, details={"old_name": old_name, "new_name": name})
    await db.commit()
    return {"id": str(org.id), "name": org.name, "slug": org.slug, "created_at": org.created_at, "is_active": org.is_active}

@router.patch("/organizations/{organization_id}/status")
async def set_platform_organization_status(organization_id: UUID, payload: PlatformOrganizationStatus, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    org = await db.get(Organization, organization_id)
    if org is None: raise HTTPException(status_code=404, detail="Organization not found")
    org.is_active = payload.is_active
    if not payload.is_active:
        pending = (await db.scalars(select(Invitation).where(Invitation.organization_id == org.id, Invitation.status == "pending"))).all()
        for invitation in pending: invitation.status = "revoked"
    await record_audit_event(db, action="platform.organization_activated" if payload.is_active else "platform.organization_suspended", resource_type="organization", organization_id=org.id, actor_user_id=user.id, resource_id=org.id, details={"is_active": payload.is_active})
    await db.commit()
    return {"id": str(org.id), "name": org.name, "is_active": org.is_active}

@router.get("/admins")
async def list_platform_admins(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    rows = (await db.execute(select(PlatformAdmin, User).join(User, User.id == PlatformAdmin.user_id).order_by(User.email))).all()
    return [{"user_id": str(admin.user_id), "email": account.email, "full_name": account.full_name, "access_level": admin.access_level, "created_at": admin.created_at} for admin, account in rows]

@router.post("/admins", status_code=status.HTTP_201_CREATED)
async def add_platform_admin(payload: PlatformAdminCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    account = await db.scalar(select(User).where(func.lower(User.email) == str(payload.email).lower()))
    if account is None: raise HTTPException(status_code=404, detail="Create or invite this user first; no account exists for that email")
    existing = await db.get(PlatformAdmin, account.id)
    if existing: raise HTTPException(status_code=409, detail="This user is already a Platform Super Admin")
    db.add(PlatformAdmin(user_id=account.id, access_level="super_admin"))
    await record_audit_event(db, action="platform.admin_granted", resource_type="platform_admin", actor_user_id=user.id, resource_id=account.id, details={"email": account.email})
    await db.commit()
    return {"user_id": str(account.id), "email": account.email, "full_name": account.full_name, "access_level": "super_admin"}

@router.delete("/admins/{admin_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_platform_admin(admin_user_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    if admin_user_id == user.id: raise HTTPException(status_code=400, detail="You cannot remove your own Platform Super Admin access")
    admin = await db.get(PlatformAdmin, admin_user_id)
    if admin is None: raise HTTPException(status_code=404, detail="Platform administrator not found")
    count = await db.scalar(select(func.count(PlatformAdmin.user_id))) or 0
    if count <= 1: raise HTTPException(status_code=409, detail="At least one Platform Super Admin must remain")
    await db.delete(admin)
    await record_audit_event(db, action="platform.admin_revoked", resource_type="platform_admin", actor_user_id=user.id, resource_id=admin_user_id)
    await db.commit()