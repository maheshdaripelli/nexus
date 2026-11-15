import re, uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate

router = APIRouter(prefix="/organizations", tags=["Organizations"])

def make_slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "organization"
    return f"{base}-{uuid.uuid4().hex[:8]}"

async def require_membership(db: AsyncSession, org_id: UUID, user_id: UUID):
    membership = await db.scalar(select(Membership).where(Membership.organization_id == org_id, Membership.user_id == user_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return membership

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(payload: OrganizationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    org = Organization(name=payload.name.strip(), slug=make_slug(payload.name))
    db.add(org)
    await db.flush()
    db.add(Membership(organization_id=org.id, user_id=current_user.id, role="owner"))
    await db.commit()
    await db.refresh(org)
    return org

@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.scalars(select(Organization).join(Membership).where(Membership.user_id == current_user.id).order_by(Organization.created_at.desc()))
    return list(result.all())

@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(organization_id: UUID, payload: OrganizationUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = await require_membership(db, organization_id, current_user.id)
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="You do not have permission to update this organization")
    org = await db.get(Organization, organization_id)
    org.name = payload.name.strip()
    await db.commit()
    await db.refresh(org)
    return org
