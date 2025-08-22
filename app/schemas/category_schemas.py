from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import UUID4, BaseModel

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

    def to_model(self, current_user_id: UUID):
        return Category(
            user_id=current_user_id,
            name=self.name,
            icon=self.icon,
            color=self.color,
            created_at=datetime.now(timezone.utc),
        )
