from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class TagBase(BaseModel):
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class TagResponse(TagBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

class TagListResponse(BaseModel):
    tags: List[TagResponse]
    total: int 

    def __init__(self, tags: List[TagResponse]):
        self.tags = tags
        self.total = len(tags)