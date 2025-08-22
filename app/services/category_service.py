import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.category import Category
from app.repository.category_repository import CategoryRepository
from app.schemas.category_schemas import CategoryUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CategoryService(BaseService[Category]):
    def __init__(self, db: Session) -> None:
        repository = CategoryRepository(db)
        super().__init__(db, repository, Category)

    def before_delete(self, id: UUID, **kwargs: Any) -> Category:
        # Basic validation
        category = super().before_delete(id, **kwargs)

        # Getting kwargs
        user_id = kwargs.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Specific Validations
        if category.user_id != user_id:
            logger.warning(
                f"Attempt to delete category with ID: {id} not owned by user with ID: {user_id}"
            )
            raise HTTPException(status_code=403, detail="You do not own this category")

        return category

    def before_update(self, id: UUID, obj_in: Any, **kwargs: Any) -> bool:
        # Basic validation
        super().before_update(id, obj_in, **kwargs)

        # Getting kwargs
        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to update category with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Get the category to check ownership
        category = self.repository.get(id)
        if category and category.user_id != user_id:
            logger.warning(
                f"Attempt to update category with ID: {id} not owned by user with ID: {user_id}"
            )
            raise HTTPException(status_code=403, detail="You do not own this category")

        return True
