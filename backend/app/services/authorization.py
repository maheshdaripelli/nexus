from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.role import Permission, RolePermission


BUILTIN_PERMISSIONS = {
    "owner": {"*"},
    "admin": {"*"},
    "manager": {"members.read", "teams.read", "teams.manage", "audit.read"},
    "member": {"members.read", "teams.read"},
    "viewer": {"members.read", "teams.read"},
}


async def require_permission(
    db: AsyncSession,
    organization_id: UUID,
    user_id: UUID,
    permission: str,
) -> Membership:
    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    granted = BUILTIN_PERMISSIONS.get(membership.role, set())
    if "*" in granted or permission in granted:
        return membership

    if membership.custom_role_id is not None:
        allowed = await db.scalar(
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == membership.custom_role_id,
                Permission.key == permission,
            )
        )
        if allowed is not None:
            return membership

    raise HTTPException(status_code=403, detail=f"Permission required: {permission}")
