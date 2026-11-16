from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class MemberRoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|manager|member|viewer)$")

class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    created_at: datetime
    email: EmailStr
    full_name: str

class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|manager|member|viewer)$")

class InvitationResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    status: str
    expires_at: datetime
    invitation_token: str
