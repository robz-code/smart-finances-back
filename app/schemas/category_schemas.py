from os import name
from typing import List, Optional
from pydantic import BaseModel, UUID4, Field
from app.entities.category import Category
from datetime import datetime, UTC
from uuid import UUID

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
            created_at=datetime.now(UTC),
            updated_at=None
        )