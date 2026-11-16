from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.schemas.organization import OrganizationCreate
from app.services.audit import record_audit_event
from app.api.v1.organizations import make_slug

router = APIRouter(prefix="/platform", tags=["Platform administration"])

class PlatformOrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    owner_email: str = Field(min_length=3, max_length=320)

async def require_platform_admin(db: AsyncSession, user_id):
    admin = await db.get(PlatformAdmin, user_id)
    if admin is None:
        raise HTTPException(status_code=403, detail="Platform administrator access required")
    return admin

@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_platform_organization(payload: PlatformOrganizationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    owner_email = payload.owner_email.strip().lower()
    owner = await db.scalar(select(User).where(User.email == owner_email, User.is_active.is_(True)))
    if owner is None:
        raise HTTPException(status_code=404, detail="An active user with that email was not found. Ask them to register first.")
    existing = await db.scalar(select(Membership.id).where(Membership.user_id == owner.id, Membership.role == "owner"))
    if existing:
        # A user can own multiple organizations only if explicitly provisioned by platform admin.
        pass
    org = Organization(name=payload.name.strip(), slug=make_slug(payload.name))
    db.add(org)
    await db.flush()
    db.add(Membership(organization_id=org.id, user_id=owner.id, role="owner"))
    await record_audit_event(db, action="organization.created", resource_type="organization", organization_id=org.id, actor_user_id=user.id, resource_id=org.id, details={"name": org.name, "owner_email": owner_email})
    await db.commit()
    await db.refresh(org)
    return {"id": str(org.id), "name": org.name, "slug": org.slug, "created_at": org.created_at, "owner_email": owner_email}

@router.get("/overview")
async def platform_overview(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    organization_count = await db.scalar(select(func.count(Organization.id))) or 0
    user_count = await db.scalar(select(func.count(User.id))) or 0
    membership_count = await db.scalar(select(func.count(Membership.id))) or 0
    return {"organization_count": organization_count, "user_count": user_count, "membership_count": membership_count}

@router.get("/organizations")
async def list_all_organizations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    statement = (select(Organization, func.count(Membership.id).label("member_count")).outerjoin(Membership, Membership.organization_id == Organization.id).group_by(Organization.id).order_by(Organization.created_at.desc()))
    rows = (await db.execute(statement)).all()
    return [{"id": str(org.id), "name": org.name, "slug": org.slug, "created_at": org.created_at, "member_count": count} for org, count in rows]
