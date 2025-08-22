import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.entities.tags import Tag
from app.repository.tag_repository import TagRepository
from app.schemas.tag_schemas import TagUpdate
from app.services.base_service import BaseService

# Configure logger
logger = logging.getLogger(__name__)


class TagService(BaseService[Tag]):
    def __init__(self, db):
        self.repository = TagRepository(db)
        self.entity = Tag
        super().__init__(db, self.repository, self.entity)

    def before_delete(self, id: UUID, **kwargs) -> bool:
        # Baisc validation
        tag = super().before_delete(id)

        # Getting kwargs
        user_id = kwargs.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Specific Validations
        if tag.user_id != user_id:
            logger.warning(
                f"Attempt to delete tag with ID: {id} not owned by user with ID: {user_id}"
            )
            raise HTTPException(status_code=403, detail="You do not own this tag")

        return tag

    def before_update(self, id: UUID, tag_in: TagUpdate, **kwargs) -> Optional[Tag]:
        # Baisc validation
        tag = super().before_update(id, tag_in)

        # Getting kwargs
        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to update tag with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Specific Validations
        if tag.user_id != user_id:
            logger.warning(
                f"Attempt to delete tag with ID: {id} not owned by user with ID: {user_id}"
            )
            raise HTTPException(status_code=403, detail="You do not own this tag")

        return tag
