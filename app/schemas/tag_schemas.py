from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.entities.tags import Tag


class TagBase(BaseModel):
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True


class TagCreate(TagBase):
    pass

    def to_model(self, user_id: UUID):
        return Tag(
            name=self.name,
            color=self.color,
            user_id=user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class TagResponse(TagBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
