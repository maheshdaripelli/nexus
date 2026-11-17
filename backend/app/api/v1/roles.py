from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.membership import Membership
from app.models.role import Permission, Role, RolePermission
from app.models.user import User
from app.services.audit import record_audit_event

router = APIRouter(prefix="/organizations/{organization_id}/roles", tags=["Roles and permissions"])

class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=300)

class RolePermissionUpdate(BaseModel):
    permission_ids: list[UUID]

async def require_admin(db: AsyncSession, org_id: UUID, user_id: UUID):
    membership = await db.scalar(select(Membership).where(Membership.organization_id == org_id, Membership.user_id == user_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization admin permission required")

@router.get("")
async def list_roles(organization_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    membership = await db.scalar(select(Membership.id).where(Membership.organization_id == organization_id, Membership.user_id == user.id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    roles = (await db.scalars(select(Role).where(Role.organization_id == organization_id).order_by(Role.name))).all()
    result = []
    for role in roles:
        keys = (await db.scalars(select(Permission.key).join(RolePermission, RolePermission.permission_id == Permission.id).where(RolePermission.role_id == role.id))).all()
        result.append({"id": role.id, "name": role.name, "description": role.description, "is_system": role.is_system, "permissions": list(keys)})
    return result

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(organization_id: UUID, payload: RoleCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_admin(db, organization_id, user.id)
    role = Role(organization_id=organization_id, name=payload.name.strip(), description=payload.description, is_system=False)
    db.add(role)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A role with this name already exists") from exc
    await record_audit_event(db, action="role.created", resource_type="role", organization_id=organization_id, actor_user_id=user.id, resource_id=role.id, details={"name": role.name})
    await db.commit()
    await db.refresh(role)
    return {"id": role.id, "name": role.name, "description": role.description, "permissions": []}

@router.put("/{role_id}/permissions")
async def set_role_permissions(organization_id: UUID, role_id: UUID, payload: RolePermissionUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_admin(db, organization_id, user.id)
    role = await db.scalar(select(Role).where(Role.id == role_id, Role.organization_id == organization_id))
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    permissions = (await db.scalars(select(Permission).where(Permission.id.in_(payload.permission_ids)))).all() if payload.permission_ids else []
    if len(permissions) != len(set(payload.permission_ids)):
        raise HTTPException(status_code=400, detail="One or more permissions do not exist")
    await db.execute(RolePermission.__table__.delete().where(RolePermission.role_id == role.id))
    db.add_all([RolePermission(role_id=role.id, permission_id=p.id) for p in permissions])
    await record_audit_event(db, action="role.permissions_updated", resource_type="role", organization_id=organization_id, actor_user_id=user.id, resource_id=role.id, details={"permission_keys": [p.key for p in permissions]})
    await db.commit()
    return {"role_id": role.id, "permissions": [p.key for p in permissions]}

@router.get("/available-permissions")
async def list_permissions(organization_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    membership = await db.scalar(select(Membership.id).where(Membership.organization_id == organization_id, Membership.user_id == user.id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    permissions = (await db.scalars(select(Permission).order_by(Permission.key))).all()
    return [{"id": p.id, "key": p.key, "description": p.description} for p in permissions]


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    organization_id: UUID,
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await require_admin(db, organization_id, user.id)
    role = await db.scalar(
        select(Role).where(Role.id == role_id, Role.organization_id == organization_id)
    )
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="System roles cannot be deleted")
    await record_audit_event(
        db,
        action="role.deleted",
        resource_type="role",
        organization_id=organization_id,
        actor_user_id=user.id,
        resource_id=role.id,
        details={"name": role.name},
    )
    await db.delete(role)
    await db.commit()
