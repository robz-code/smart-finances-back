import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.concept import Concept
from app.repository.concept_repository import ConceptRepository

# from app.schemas.concept_schemas import ConceptUpdate  # unused in service
from app.services.base_service import BaseService

# Configure logger
logger = logging.getLogger(__name__)


class ConceptService(BaseService[Concept]):
    def __init__(self, db: Session) -> None:
        self.repository = ConceptRepository(db)
        self.entity = Concept
        super().__init__(db, self.repository, self.entity)

    def before_delete(self, id: UUID, **kwargs: Any) -> Concept:
        # Basic validation
        concept = super().before_delete(id, **kwargs)

        # Getting kwargs
        user_id = kwargs.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Specific Validations
        if concept.user_id != user_id:
            logger.warning(
                (
                    f"Attempt to delete concept with ID: {id} not owned by user "
                    f"with ID: {user_id}"
                )
            )
            raise HTTPException(status_code=403, detail="You do not own this concept")

        return concept

    def before_update(self, id: UUID, obj_in: Any, **kwargs: Any) -> bool:
        # Basic validation
        super().before_update(id, obj_in, **kwargs)

        # Getting kwargs
        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to update concept with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Get the concept to check ownership
        concept = self.repository.get(id)
        if concept and concept.user_id != user_id:
            logger.warning(
                (
                    f"Attempt to update concept with ID: {id} not owned by user "
                    f"with ID: {user_id}"
                )
            )
            raise HTTPException(status_code=403, detail="You do not own this concept")

        return True
