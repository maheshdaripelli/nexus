from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)

class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    created_at: datetime
