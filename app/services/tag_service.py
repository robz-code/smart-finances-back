from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.repository.tag_repository import TagRepository
from app.schemas.tag_schemas import TagCreate, TagUpdate, TagResponse
from app.entities.tags import Tag
from app.services.base_service import BaseService
class TagService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.repository = TagRepository(db)