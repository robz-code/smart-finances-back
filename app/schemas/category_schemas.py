import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import UUID4, BaseModel, field_validator

from app.entities.category import Category


class CategoryUpdate(BaseModel):
    name: Optional[str]
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    id: UUID4
    name: str
    icon: str
    color: str
    created_at: datetime
    updated_at: datetime


class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None

    def to_model(self, current_user_id: UUID) -> Category:
        return Category(
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

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Category name must be at least 2 characters long")
        if len(v.strip()) > 100:
            raise ValueError("Category name cannot exceed 100 characters")
        # Check for valid characters (letters, numbers, spaces, hyphens)
        if not re.match(r"^[a-zA-ZÀ-ÿ0-9\s\-]+$", v.strip()):
            raise ValueError(
                "Category name can only contain letters, numbers, spaces, and hyphens"
            )
        return v.strip()
