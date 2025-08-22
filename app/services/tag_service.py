import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.tags import Tag
from app.repository.tag_repository import TagRepository
from app.schemas.tag_schemas import TagUpdate
from app.services.base_service import BaseService

# Configure logger
logger = logging.getLogger(__name__)


class TagService(BaseService[Tag]):
    def __init__(self, db: Session) -> None:
        self.repository = TagRepository(db)
        self.entity = Tag
        super().__init__(db, self.repository, self.entity)

    def before_delete(self, id: UUID, **kwargs: Any) -> Tag:
        # Basic validation
        tag = super().before_delete(id, **kwargs)

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

    def before_update(self, id: UUID, obj_in: Any, **kwargs: Any) -> bool:
        # Basic validation
        super().before_update(id, obj_in, **kwargs)

        # Getting kwargs
        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to update tag with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Get the tag to check ownership
        tag = self.repository.get(id)
        if tag and tag.user_id != user_id:
            logger.warning(
                f"Attempt to update tag with ID: {id} not owned by user with ID: {user_id}"
            )
            raise HTTPException(status_code=403, detail="You do not own this tag")

        return True
