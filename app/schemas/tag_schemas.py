import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.entities.tags import Tag


class TagBase(BaseModel):
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Tag name must be at least 2 characters long")
        if len(v.strip()) > 50:
            raise ValueError("Tag name cannot exceed 50 characters")
        # Check for valid characters (letters, numbers, spaces, hyphens)
        if not re.match(r"^[a-zA-ZÀ-ÿ0-9\s\-]+$", v.strip()):
            raise ValueError(
                "Tag name can only contain letters, numbers, spaces, and hyphens"
            )
        return v.strip()


class TagCreate(TagBase):
    pass

    def to_model(self, user_id: UUID) -> Tag:
        return Tag(
            name=self.name,
            color=self.color,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class TagResponse(TagBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    def to_model(self, current_user_id: UUID) -> Tag:
        return Tag(
            id=current_user_id,
            name=self.name,
            color=self.color,
            created_at=datetime.now(timezone.utc),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "color": self.color,
            "created_at": datetime.now(timezone.utc),
        }


class TagTransactionCreate(TagCreate):
    id: Optional[UUID] = None
