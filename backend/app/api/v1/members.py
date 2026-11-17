import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
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
from app.services.email import send_invitation_email
from app.core.config import settings
from app.services.authorization import require_permission

router = APIRouter(prefix="/organizations/{organization_id}", tags=["Organization members"])

async def admin_membership(db: AsyncSession, org_id: UUID, user_id: UUID):
    membership = await db.scalar(select(Membership).where(Membership.organization_id == org_id, Membership.user_id == user_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return await require_permission(db, org_id, user_id, "members.manage")

@router.get("/members", response_model=list[MemberResponse])
async def list_members(organization_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await require_permission(db, organization_id, user.id, "members.read")
    rows = (await db.execute(select(Membership, User).join(User, User.id == Membership.user_id).where(Membership.organization_id == organization_id).order_by(Membership.created_at))).all()
    return [MemberResponse(id=m.id, organization_id=m.organization_id, user_id=m.user_id, role=m.role, custom_role_id=m.custom_role_id, created_at=m.created_at, email=u.email, full_name=u.full_name) for m,u in rows]

@router.patch("/members/{user_id}", response_model=MemberResponse)
async def update_member_role(organization_id: UUID, user_id: UUID, payload: MemberRoleUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    actor = await admin_membership(db, organization_id, user.id)
    target = await db.scalar(select(Membership).where(Membership.organization_id == organization_id, Membership.user_id == user_id))
    if target is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if target.role == "owner":
        raise HTTPException(status_code=403, detail="The organization owner role cannot be changed here")
    if payload.custom_role_id is not None:
        custom_role = await db.scalar(select(Role).where(Role.id == payload.custom_role_id, Role.organization_id == organization_id))
        if custom_role is None:
            raise HTTPException(status_code=404, detail="Custom role not found in this organization")
        if actor.role != "owner" and target.role == "admin":
            raise HTTPException(status_code=403, detail="Only the owner can change admin privileges")
        target.custom_role_id = custom_role.id
        target.role = "custom"
    elif payload.role is not None:
        if actor.role != "owner" and payload.role == "admin":
            raise HTTPException(status_code=403, detail="Only the owner can assign admin privileges")
        target.role = payload.role
        target.custom_role_id = None
    else:
        raise HTTPException(status_code=400, detail="Provide either a built-in role or a custom_role_id")
    await record_audit_event(db, action="member.role_updated", resource_type="membership", organization_id=organization_id, actor_user_id=user.id, resource_id=target.id, details={"target_user_id": str(user_id), "role": target.role, "custom_role_id": str(target.custom_role_id) if target.custom_role_id else None})
    await db.commit()
    member = await db.get(User, user_id)
    return MemberResponse(id=target.id, organization_id=target.organization_id, user_id=target.user_id, role=target.role, custom_role_id=target.custom_role_id, created_at=target.created_at, email=member.email, full_name=member.full_name)

@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(organization_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    actor = await admin_membership(db, organization_id, user.id)
    target = await db.scalar(select(Membership).where(Membership.organization_id == organization_id, Membership.user_id == user_id))
    if target is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if target.role == "owner" or (actor.role != "owner" and target.role == "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permission to remove this member")
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="Use organization ownership transfer before leaving as owner")
    await record_audit_event(db, action="member.removed", resource_type="membership", organization_id=organization_id, actor_user_id=user.id, resource_id=target.id, details={"target_user_id": str(user_id)})
    await db.delete(target)
    await db.commit()

@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(organization_id: UUID, payload: InvitationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
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
    invitation_url = (
        f"{settings.FRONTEND_ORIGIN.rstrip('/')}/accept-invitation"
        f"?organization_id={organization_id}&token={raw_token}"
    )
    email_sent = await send_invitation_email(
        to_email=email,
        organization_name=org.name,
        role=payload.role,
        invitation_url=invitation_url,
        expires_at=invitation.expires_at.isoformat(),
    )
    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        invitation_token=raw_token,
        email_sent=email_sent,
    )

@router.post("/invitations/accept")
async def accept_invitation(token: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invitation = await db.scalar(select(Invitation).where(Invitation.token_hash == token_hash, Invitation.status == "pending").with_for_update())
    if invitation is None or invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invitation is invalid or expired")
    if user.email.lower() != invitation.email.lower():
        raise HTTPException(status_code=403, detail="Invitation email does not match signed-in account")
    exists = await db.scalar(select(Membership.id).where(Membership.organization_id == invitation.organization_id, Membership.user_id == user.id))
    if exists:
        raise HTTPException(status_code=409, detail="Already a member of this organization")
    db.add(Membership(organization_id=invitation.organization_id, user_id=user.id, role=invitation.role))
    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(timezone.utc)
    await record_audit_event(db, action="invitation.accepted", resource_type="invitation", organization_id=invitation.organization_id, actor_user_id=user.id, resource_id=invitation.id, details={"email": invitation.email})
    await db.commit()
    return {"organization_id": str(invitation.organization_id), "message": "Invitation accepted"}


@router.get("/invitations")
async def list_invitations(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await admin_membership(db, organization_id, user.id)
    rows = (await db.scalars(
        select(Invitation)
        .where(Invitation.organization_id == organization_id)
        .order_by(Invitation.created_at.desc())
    )).all()
    now = datetime.now(timezone.utc)
    return [
        {
            "id": str(row.id),
            "email": row.email,
            "role": row.role,
            "status": "expired" if row.status == "pending" and row.expires_at <= now else row.status,
            "expires_at": row.expires_at,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    organization_id: UUID,
    invitation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await admin_membership(db, organization_id, user.id)
    invitation = await db.scalar(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.organization_id == organization_id,
        ).with_for_update()
    )
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.status != "pending" or invitation.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="Only active pending invitations can be revoked")
    invitation.status = "revoked"
    await record_audit_event(
        db,
        action="invitation.revoked",
        resource_type="invitation",
        organization_id=organization_id,
        actor_user_id=user.id,
        resource_id=invitation.id,
        details={"email": invitation.email},
    )
    await db.commit()
