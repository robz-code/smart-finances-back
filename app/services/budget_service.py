import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.budget import Budget
from app.repository.budget_repository import BudgetRepository
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class BudgetService(BaseService[Budget]):
    def __init__(self, db: Session) -> None:
        repository = BudgetRepository(db)
        super().__init__(db, repository, Budget)

    def before_update(self, id: UUID, obj_in: Any, **kwargs: Any) -> bool:
        super().before_update(id, obj_in, **kwargs)

        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to update budget with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Get the budget to check ownership
        budget = self.repository.get(id)
        if budget and budget.user_id != user_id:
            logger.warning(
                (
                    f"Attempt to update budget with ID: {id} not owned by user "
                    f"with ID: {user_id}"
                )
            )
            raise HTTPException(status_code=403, detail="You do not own this budget")

        return True

    def before_delete(self, id: UUID, **kwargs: Any) -> Budget:
        budget = super().before_delete(id, **kwargs)

        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to delete budget with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        if budget.user_id != user_id:
            logger.warning(
                (
                    f"Attempt to delete budget with ID: {id} not owned by user "
                    f"with ID: {user_id}"
                )
            )
            raise HTTPException(status_code=403, detail="You do not own this budget")

        return budget
