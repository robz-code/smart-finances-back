import logging
from typing import Generic, Type, TypeVar
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase

from app.schemas.base_schemas import SearchResponse

T = TypeVar("T", bound=DeclarativeBase)

logger = logging.getLogger(__name__)


class BaseService(Generic[T]):
    def __init__(self, db, repository, entity: Type[T]):
        self.db = db
        self.repository = repository
        self.entity = entity

    def get(self, id: UUID) -> T:
        """Get entity by ID with error handling"""

        try:
            obj = self.repository.get(id)
            if obj is None:
                logger.warning(f"{self.entity.__name__} not found with ID: {id}")
                raise HTTPException(
                    status_code=404, detail=f"{self.entity.__name__} not found"
                )
            return obj
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(
                f"Database error in get for {self.entity.__name__} ID {id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(
                f"Unexpected error in get for {self.entity.__name__} ID {id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Internal server error")

    def get_by_user_id(self, user_id: UUID) -> SearchResponse[T]:
        """Get entities by user ID with error handling"""

        try:
            result = self.repository.get_by_user_id(user_id)
            return SearchResponse(total=len(result), results=result)
        except SQLAlchemyError as e:
            logger.error(
                f"Database error in get_by_user_id for {self.entity.__name__}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(
                f"Unexpected error in get_by_user_id for {self.entity.__name__}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Internal server error")

    def delete(self, id: UUID, **kwargs) -> T:
        """Delete entity by ID with error handling"""

        self.before_delete(id, **kwargs)
        try:
            deleted_obj = self.repository.delete(id)
            logger.info(f"Successfully deleted {self.entity.__name__} with ID: {id}")
            return deleted_obj
        except HTTPException:
            raise
        except IntegrityError as e:
            logger.error(
                f"Integrity error deleting {self.entity.__name__} ID {id}: {str(e)}"
            )
            raise HTTPException(
                status_code=409,
                detail="Cannot delete due to existing references",
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Database error deleting {self.entity.__name__} ID {id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(
                f"Unexpected error deleting {self.entity.__name__} ID {id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Internal server error")

    def add(self, obj_in: T, **kwargs) -> T:
        """Add new entity with error handling"""

        self.before_create(obj_in, **kwargs)
        try:
            result = self.repository.add(obj_in)
            logger.info(
                f"Successfully created {self.entity.__name__} with ID: {result.id}"
            )
            return result
        except IntegrityError as e:
            logger.error(f"Integrity error creating {self.entity.__name__}: {str(e)}")
            if "unique" in str(e).lower():
                raise HTTPException(status_code=409, detail="Entity already exists")
            raise HTTPException(status_code=400, detail="Invalid data provided")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating {self.entity.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error creating {self.entity.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def update(self, id: UUID, obj_in: T, **kwargs) -> T:
        """Update entity by ID with error handling"""

        self.before_update(id, obj_in, **kwargs)
        try:
            result = self.repository.update(id, obj_in)
            logger.info(f"Successfully updated {self.entity.__name__} with ID: {id}")
            return result
        except HTTPException:
            raise
        except IntegrityError as e:
            logger.error(
                f"Integrity error updating {self.entity.__name__} ID {id}: {str(e)}"
            )
            if "unique" in str(e).lower():
                raise HTTPException(
                    status_code=409,
                    detail="Update would violate unique constraint",
                )
            raise HTTPException(status_code=400, detail="Invalid data provided")
        except SQLAlchemyError as e:
            logger.error(
                f"Database error updating {self.entity.__name__} ID {id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(
                f"Unexpected error updating {self.entity.__name__} ID {id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Internal server error")

    # Hooks
    def before_create(self, obj_in: T, **kwargs) -> bool:
        """Perform actions before the entity is created"""

        return True

    def before_update(self, id: UUID, obj_in: T, **kwargs) -> bool:
        """Perform actions before the entity is created or updated"""
        obj = self.repository.get(id)
        if obj is None:
            logger.warning(
                f"Attempt to update non-existent {self.entity.__name__} with ID: {id}"
            )
            raise HTTPException(
                status_code=404, detail=f"{self.entity.__name__} not found"
            )

        return obj

    def before_delete(self, id: UUID, **kwargs) -> T:
        """Perform actions after the entity is created"""
        # Check if the entity exists
        obj = self.repository.get(id)
        if obj is None:
            logger.warning(
                f"Attempt to delete non-existent {self.entity.__name__} with ID: {id}"
            )
            raise HTTPException(
                status_code=404, detail=f"{self.entity.__name__} not found"
            )

        return obj
