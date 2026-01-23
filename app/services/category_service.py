import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.category import Category, CategoryType
from app.repository.category_repository import CategoryRepository
from app.schemas.base_schemas import SearchResponse
from app.schemas.category_schemas import CategoryCreate

# from app.schemas.category_schemas import CategoryUpdate  # unused in service
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CategoryService(BaseService[Category]):
    def __init__(self, db: Session) -> None:
        repository = CategoryRepository(db)
        super().__init__(db, repository, Category)

    # def get_by_user_id(self, user_id):
    #     categories = super().get_by_user_id(user_id)
    #     # Exclude transfer category
    #     categories = [cat for cat in categories if cat.type != "transfer"]
    #     return categories

    def get_transfer_category(self, user_id: UUID) -> Category:
        """
        Get the transfer category for a user.

        Returns:
            The transfer category for the user.
        """
        category = self.repository.get_transfer_category(user_id)

        if not category:
            category = self.add(CategoryCreate(name="transfer").to_model(user_id))

        return category

    def get_by_user_id_and_type(
        self, user_id: UUID, category_type: CategoryType
    ) -> SearchResponse[Category]:
        categories = self.repository.get_by_user_id_and_type(
            user_id, category_type.value
        )
        return SearchResponse(total=len(categories), results=categories)

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
                (
                    f"Attempt to delete category with ID: {id} not owned by user "
                    f"with ID: {user_id}"
                )
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
                (
                    f"Attempt to update category with ID: {id} not owned by user "
                    f"with ID: {user_id}"
                )
            )
            raise HTTPException(status_code=403, detail="You do not own this category")

        return True
