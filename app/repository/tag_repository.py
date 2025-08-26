from sqlalchemy.orm import Session

from app.entities.tags import Tag
from app.repository.base_repository import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Tag)
