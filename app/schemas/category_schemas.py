

from typing import List, Optional
from pydantic import BaseModel, UUID4, Field
import datetime
from app.entities.category import Category

class CategoryCreate(BaseModel):
    name: str
    user_id: UUID4

class CategoryUpdate(BaseModel):
    name: Optional[str]

class CategoryResponse(BaseModel):
    id: UUID4
    name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    user_id: UUID4
