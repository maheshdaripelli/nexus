from datetime import datetime,timedelta,timezone
import hashlib
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token,create_refresh_token,hash_password,hash_refresh_token,verify_password
from app.db.session import get_db
from app.models.invitation import Invitation
from app.models.membership import Membership
from app.models.refresh_token import RefreshToken
from app.models.organization import Organization
from app.models.user import User
from app.services.audit import record_audit_event
from app.schemas.auth import LoginRequest,RefreshRequest,TokenResponse,UserProfileUpdate,UserResponse
router=APIRouter(prefix="/auth",tags=["Authentication"])
class InvitationRegistration(BaseModel):
 token:str=Field(min_length=20,max_length=256)
 full_name:str=Field(min_length=2,max_length=120)
 password:str=Field(min_length=12,max_length=128)
async def issue_tokens(db:AsyncSession,user:User)->TokenResponse:
 raw=create_refresh_token()
 db.add(RefreshToken(user_id=user.id,token_hash=hash_refresh_token(raw),expires_at=datetime.now(timezone.utc)+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)))
 await db.commit()
 return TokenResponse(access_token=create_access_token(user.id),refresh_token=raw,user=user)
@router.post("/register",status_code=403)
async def public_registration_disabled():
 raise HTTPException(status_code=403,detail="Public registration is disabled. A valid organization invitation is required.")
@router.post("/register-from-invitation",response_model=TokenResponse,status_code=201)
async def register_from_invitation(payload:InvitationRegistration,db:AsyncSession=Depends(get_db)):
 digest=hashlib.sha256(payload.token.encode()).hexdigest()
 invitation=await db.scalar(select(Invitation).where(Invitation.token_hash==digest,Invitation.status=="pending").with_for_update())
 now=datetime.now(timezone.utc)
 if invitation is None or invitation.expires_at<=now: raise HTTPException(status_code=400,detail="Invitation is invalid, expired, or already used")
 organization=await db.get(Organization,invitation.organization_id)
 if organization is None or not organization.is_active: raise HTTPException(status_code=403,detail="This organization is currently suspended")
 email=invitation.email.strip().lower()
 if await db.scalar(select(User.id).where(User.email==email)): raise HTTPException(status_code=409,detail="An account already exists for this email. Sign in and accept the invitation.")
 user=User(email=email,full_name=payload.full_name.strip(),password_hash=hash_password(payload.password),is_active=True)
 db.add(user);await db.flush()
 db.add(Membership(organization_id=invitation.organization_id,user_id=user.id,role=invitation.role))
 invitation.status="accepted";invitation.accepted_at=now
 await record_audit_event(db,action="invitation.accepted",resource_type="invitation",organization_id=invitation.organization_id,actor_user_id=user.id,resource_id=invitation.id,details={"email":email,"role":invitation.role})
 await db.flush()
 return await issue_tokens(db,user)
@router.post("/login",response_model=TokenResponse)
async def login(payload:LoginRequest,db:AsyncSession=Depends(get_db)):
 user=await db.scalar(select(User).where(User.email==str(payload.email).lower()))
 if user is None or not user.is_active or not verify_password(payload.password,user.password_hash): raise HTTPException(status_code=401,detail="Incorrect email or password",headers={"WWW-Authenticate":"Bearer"})
 return await issue_tokens(db,user)
@router.post("/refresh",response_model=TokenResponse)
async def refresh(payload:RefreshRequest,db:AsyncSession=Depends(get_db)):
 stored=await db.scalar(select(RefreshToken).where(RefreshToken.token_hash==hash_refresh_token(payload.refresh_token),RefreshToken.revoked.is_(False)).with_for_update())
 now=datetime.now(timezone.utc)
 if stored is None or stored.expires_at<=now: raise HTTPException(status_code=401,detail="Refresh token is invalid or expired")
 user=await db.get(User,stored.user_id)
 if user is None or not user.is_active: raise HTTPException(status_code=401,detail="Account is unavailable")
 stored.revoked=True
 return await issue_tokens(db,user)
@router.post("/logout",status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload:RefreshRequest,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
 stored=await db.scalar(select(RefreshToken).where(RefreshToken.token_hash==hash_refresh_token(payload.refresh_token),RefreshToken.user_id==user.id))
 if stored is not None: stored.revoked=True;await db.commit()
@router.get("/me",response_model=UserResponse)
async def me(current_user:User=Depends(get_current_user)): return current_user

@router.patch("/me",response_model=UserResponse)
async def update_profile(payload:UserProfileUpdate,db:AsyncSession=Depends(get_db),current_user:User=Depends(get_current_user)):
 current_user.full_name=payload.full_name
 await db.commit()
 await db.refresh(current_user)
 return current_user
