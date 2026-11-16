from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

async def record_audit_event(
    db: AsyncSession,
    *,
    action: str,
    resource_type: str,
    organization_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    resource_id: str | UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Add an audit event to the current transaction; caller commits."""
    db.add(AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=details or {},
        ip_address=ip_address,
    ))
