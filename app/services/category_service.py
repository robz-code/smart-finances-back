import logging
from typing import Any, Optional
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

        # Block deletion if transactions exist — require migration first
        count = self.repository.count_transactions(id)
        if count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Category has {count} transaction(s). Migrate them before deleting.",
            )

        return category

    def migrate(self, source_id: UUID, target_id: UUID, user_id: UUID) -> Optional[int]:
        """Reassign all transactions from source_category to target_category.

        Validates:
        - Both categories exist (404)
        - Both categories are owned by the same user (403)
        - Both categories share the same type (422 if mismatched)

        Returns the number of transactions migrated.
        """
        # Fetch source — 404 if not found
        source = self.repository.get(source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="Source category not found")
        if source.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="You do not own the source category"
            )

        # Fetch target — 404 if not found
        target = self.repository.get(target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="Target category not found")
        if target.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="You do not own the target category"
            )

        # Type must match — cannot migrate expense transactions into an income category
        if source.type != target.type:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Cannot migrate: source category type '{source.type}' does not "
                    f"match target category type '{target.type}'."
                ),
            )

        migrated = self.repository.migrate_transactions(source_id, target_id)
        logger.info(
            f"Migrated {migrated} transaction(s) from category {source_id} → {target_id}"
        )
        return migrated

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
