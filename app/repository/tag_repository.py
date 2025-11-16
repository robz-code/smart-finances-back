from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.tags import Tag
from app.repository.base_repository import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Tag)

    def validate_tag_ownership(self, user_id: UUID, tag_id: UUID) -> bool:
        """Validate that the user owns the tag."""
        tag = self.db.query(Tag).filter(Tag.id == tag_id).first()
        return bool(tag and tag.user_id == user_id)
