import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.entities.concept import Concept


class ConceptBase(BaseModel):
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Concept name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Concept name must be at least 2 characters long")
        if len(v.strip()) > 50:
            raise ValueError("Concept name cannot exceed 50 characters")
        # Check for valid characters (letters, numbers, spaces, hyphens)
        if not re.match(r"^[a-zA-ZÀ-ÿ0-9\s\-]+$", v.strip()):
            raise ValueError(
                "Concept name can only contain letters, numbers, spaces, and hyphens"
            )
        return v.strip()


class ConceptCreate(ConceptBase):
    pass

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if v and not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", v):
            raise ValueError("Invalid color format")
        return v

    def to_model(self, user_id: UUID) -> Concept:
        return Concept(
            name=self.name,
            color=self.color,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


class ConceptUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class ConceptResponse(ConceptBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    def to_model(self, current_user_id: UUID) -> Concept:
        return Concept(
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


class ConceptTransactionCreate(BaseModel):
    id: Optional[UUID] = None
    name: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Concept name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Concept name must be at least 2 characters long")
        if len(v.strip()) > 50:
            raise ValueError("Concept name cannot exceed 50 characters")
        # Check for valid characters (letters, numbers, spaces, hyphens)
        if not re.match(r"^[a-zA-ZÀ-ÿ0-9\s\-]+$", v.strip()):
            raise ValueError(
                "Concept name can only contain letters, numbers, spaces, and hyphens"
            )
        return v.strip()

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if v and not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", v):
            raise ValueError("Invalid color format")
        return v

    def to_model(self, user_id: UUID) -> Concept:
        return Concept(
            name=self.name,
            color=self.color,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
