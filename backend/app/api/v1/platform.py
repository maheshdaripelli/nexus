from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.platform_admin import PlatformAdmin
from app.models.user import User

router = APIRouter(prefix="/platform", tags=["Platform administration"])

async def require_platform_admin(db: AsyncSession, user_id):
    admin = await db.get(PlatformAdmin, user_id)
    if admin is None:
        raise HTTPException(status_code=403, detail="Platform administrator access required")
    return admin

@router.get("/overview")
async def platform_overview(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_platform_admin(db, user.id)
    organization_count = await db.scalar(select(func.count(Organization.id))) or 0
    user_count = await db.scalar(select(func.count(User.id))) or 0
    membership_count = await db.scalar(select(func.count(Membership.id))) or 0
    return {
        "organization_count": organization_count,
        "user_count": user_count,
        "membership_count": membership_count,
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
