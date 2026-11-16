import hashlib,secrets
from datetime import datetime,timedelta,timezone
from pydantic import BaseModel,Field,EmailStr
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.invitation import Invitation
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.services.audit import record_audit_event
from app.api.v1.organizations import make_slug
router=APIRouter(prefix="/platform",tags=["Platform administration"])
class PlatformOrganizationCreate(BaseModel):
 name:str=Field(min_length=2,max_length=160)
 owner_email:EmailStr
async def require_platform_admin(db:AsyncSession,user_id):
 if await db.get(PlatformAdmin,user_id) is None: raise HTTPException(status_code=403,detail="Platform administrator access required")
@router.post("/organizations",status_code=status.HTTP_201_CREATED)
async def create_platform_organization(payload:PlatformOrganizationCreate,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
 await require_platform_admin(db,user.id)
 email=str(payload.owner_email).strip().lower()
 org=Organization(name=payload.name.strip(),slug=make_slug(payload.name));db.add(org);await db.flush()
 raw=secrets.token_urlsafe(40)
 invite=Invitation(organization_id=org.id,email=email,role="owner",token_hash=hashlib.sha256(raw.encode()).hexdigest(),invited_by_user_id=user.id,expires_at=datetime.now(timezone.utc)+timedelta(days=7))
 db.add(invite)
 await record_audit_event(db,action="organization.provisioned",resource_type="organization",organization_id=org.id,actor_user_id=user.id,resource_id=org.id,details={"name":org.name,"initial_owner_email":email})
 await db.commit();await db.refresh(org)
 return {"id":str(org.id),"name":org.name,"slug":org.slug,"created_at":org.created_at,"owner_email":email,"invitation_token":raw}
@router.get("/overview")
async def platform_overview(db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
 await require_platform_admin(db,user.id)
 return {"organization_count":await db.scalar(select(func.count(Organization.id))) or 0,"user_count":await db.scalar(select(func.count(User.id))) or 0,"membership_count":await db.scalar(select(func.count(Membership.id))) or 0}
@router.get("/organizations")
async def list_all_organizations(db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
 await require_platform_admin(db,user.id)
 statement=select(Organization,func.count(Membership.id).label("member_count")).outerjoin(Membership,Membership.organization_id==Organization.id).group_by(Organization.id).order_by(Organization.created_at.desc())
 rows=(await db.execute(statement)).all()
 return [{"id":str(o.id),"name":o.name,"slug":o.slug,"created_at":o.created_at,"member_count":count} for o,count in rows]
