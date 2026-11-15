from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)

class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=160)

class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    created_at: datetime
