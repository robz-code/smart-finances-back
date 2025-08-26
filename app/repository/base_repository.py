import logging
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session

T = TypeVar("T", bound=DeclarativeBase)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get(self, id: UUID) -> Optional[T]:
        """Get entity by ID"""
        # Handle entities that might not have an id field (like UserContact)
        if hasattr(self.model, "id"):
            return (
                self.db.query(self.model)
                .filter(self.model.id == id)
                .first()  # type: ignore
            )
        else:
            # For entities without id (like UserContact), this method might not
            # be applicable
            logger.warning(
                f"get() method called on {self.model.__name__} which has no id field"
            )
            return None

    def get_by_user_id(self, user_id: UUID) -> List[T]:
        """Get entities by user ID"""
        return (
            self.db.query(self.model)
            .filter(self.model.user_id == user_id)
            .all()  # type: ignore
        )

    def get_contacts_by_user_id(self, user_id: UUID) -> List[T]:
        """Get contact relationships by user ID
        (works with both user1_id and user2_id)"""
        return (
            self.db.query(self.model)
            .filter((self.model.user1_id == user_id) | (self.model.user2_id == user_id))
            .all()  # type: ignore
        )

    def delete(self, id: UUID) -> Optional[T]:
        """Delete entity by ID with transaction handling"""
        obj = self.get(id)
        if obj:
            try:
                self.db.delete(obj)
                self.db.commit()
                logger.info(f"Successfully deleted {self.model.__name__} with ID: {id}")
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(
                    f"Database error deleting {self.model.__name__} ID {id}: {str(e)}"
                )
                raise
        return obj

    def add(self, obj_in: T) -> T:
        """Add new entity with transaction handling"""
        try:
            self.db.add(obj_in)
            self.db.commit()
            self.db.refresh(obj_in)

            # Handle entities that might not have an id field (like UserContact)
            if hasattr(obj_in, "id"):
                logger.info(
                    f"Successfully created {self.model.__name__} "
                    f"with ID: {obj_in.id}"  # type: ignore
                )
            else:
                # For entities without id (like UserContact with composite primary key)
                logger.info(f"Successfully created {self.model.__name__}")

            return obj_in
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating {self.model.__name__}: {str(e)}")
            raise

    def update(self, id: UUID, obj_in: T) -> Optional[T]:
        """Update entity by ID with transaction handling"""
        obj = self.get(id)
        if obj:
            try:
                # Extract attributes from the model object,
                # excluding private attributes and id
                update_data = {
                    k: v
                    for k, v in obj_in.__dict__.items()
                    if not k.startswith("_") and k != "id"
                }

                # Protect audit fields from being modified
                protected_fields = {"created_at", "updated_at"}
                for field in protected_fields:
                    if field in update_data:
                        del update_data[field]

                for key, value in update_data.items():
                    if value is not None and hasattr(obj, key):
                        setattr(obj, key, value)

                # Set updated_at manually to ensure it's updated
                if hasattr(obj, "updated_at"):
                    from datetime import datetime, timezone

                    obj.updated_at = datetime.now(timezone.utc)

                self.db.commit()
                self.db.refresh(obj)
                logger.info(f"Successfully updated {self.model.__name__} with ID: {id}")
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(
                    f"Database error updating {self.model.__name__} ID {id}: {str(e)}"
                )
                raise
        return obj
