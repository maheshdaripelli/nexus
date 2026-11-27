import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.invitation import Invitation
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from app.schemas.member import InvitationCreate, InvitationResponse, MemberResponse, MemberRoleUpdate
from app.services.audit import record_audit_event
from app.api.v1.members import admin_membership
from app.core.config import settings
from app.services.authorization import require_permission


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations/{organization_id}", tags=["V2 invitations"])

class QueuedInvitationResponse(InvitationResponse):
    email_queued: bool = False

@router.post("/invitations", response_model=QueuedInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(organization_id: UUID, payload: InvitationCreate, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not settings.RABBITMQ_URL:
        raise HTTPException(status_code=503, detail="RabbitMQ is not configured")
    actor = await admin_membership(db, organization_id, user.id)
    if payload.role == "admin" and actor.role != "owner":
        raise HTTPException(status_code=403, detail="Only the organization owner can invite another admin")
    org = await db.get(Organization, organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    email = str(payload.email).lower()
    existing_user = await db.scalar(select(User).where(User.email == email))
    if existing_user and await db.scalar(select(Membership.id).where(Membership.organization_id == organization_id, Membership.user_id == existing_user.id)):
        raise HTTPException(status_code=409, detail="User is already a member")
    pending_invitation = await db.scalar(select(Invitation).where(Invitation.organization_id == organization_id, Invitation.email == email, Invitation.status == "pending").with_for_update())
    if pending_invitation is not None:
        if pending_invitation.expires_at > datetime.now(timezone.utc):
            raise HTTPException(status_code=409, detail="A pending invitation already exists for this email")
        pending_invitation.status = "expired"
    raw_token = secrets.token_urlsafe(32)
    invitation = Invitation(organization_id=organization_id, email=email, role=payload.role, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), invited_by_user_id=user.id, expires_at=datetime.now(timezone.utc)+timedelta(days=7))
    db.add(invitation)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A pending invitation already exists for this email") from exc
    await record_audit_event(db, action="invitation.created", resource_type="invitation", organization_id=organization_id, actor_user_id=user.id, resource_id=invitation.id, details={"email": email, "role": payload.role})
    await db.commit()
    await db.refresh(invitation)
    email_queued = False
    try:
        await request.app.state.rabbitmq.publish(invitation.id, raw_token)
        email_queued = True
    except Exception:
        logger.warning("Invitation publish not confirmed: %s", invitation.id)
    return QueuedInvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        invitation_token=raw_token,
        email_sent=False,
        email_queued=email_queued,
    )

