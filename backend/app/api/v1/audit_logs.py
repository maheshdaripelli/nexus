from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.membership import Membership
from app.models.user import User

router = APIRouter(prefix="/organizations/{organization_id}/audit-logs", tags=["Audit logs"])

@router.get("")
async def list_audit_logs(organization_id: UUID, limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    membership = await db.scalar(select(Membership).where(Membership.organization_id == organization_id, Membership.user_id == user.id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if membership.role not in {"owner", "admin", "manager"}:
        raise HTTPException(status_code=403, detail="Audit log access denied")
    rows = (await db.scalars(select(AuditLog).where(AuditLog.organization_id == organization_id).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset))).all()
    return [{"id": row.id, "actor_user_id": row.actor_user_id, "action": row.action, "resource_type": row.resource_type, "resource_id": row.resource_id, "details": row.details, "ip_address": row.ip_address, "created_at": row.created_at} for row in rows]
