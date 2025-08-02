from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from app.entities.tags import Tag
from app.entities.transaction_tag import TransactionTag
from app.repository.base_repository import BaseRepository

class TagRepository(BaseRepository[Tag]):
    def __init__(self, db: Session):
        super().__init__(db ,Tag)