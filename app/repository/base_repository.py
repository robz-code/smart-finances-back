from sqlalchemy.orm import Session
from uuid import UUID
from typing import TypeVar, Generic, Type, List, Optional, Any
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.schemas.base_schemas import SearchResponse

T = TypeVar('T', bound=DeclarativeBase)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get(self, id: UUID) -> Optional[T]:
        """Get entity by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_by_user_id(self, user_id: UUID) -> List[T]:
        """Get entities by user ID"""
        return self.db.query(self.model).filter(self.model.user_id == user_id).all()

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
                logger.error(f"Database error deleting {self.model.__name__} ID {id}: {str(e)}")
                raise
        return obj

    def add(self, obj_in: T) -> T:
        """Add new entity with transaction handling"""
        try:
            self.db.add(obj_in)
            self.db.commit()
            self.db.refresh(obj_in)
            logger.info(f"Successfully created {self.model.__name__} with ID: {obj_in.id}")
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
                # Extract attributes from the model object, excluding private attributes and id
                update_data = {k: v for k, v in obj_in.__dict__.items() 
                                if not k.startswith('_') and k != 'id'}
                
                # Protect audit fields from being modified
                protected_fields = {'created_at', 'updated_at'}
                for field in protected_fields:
                    if field in update_data:
                        del update_data[field]
                
                for key, value in update_data.items():
                    if value is not None and hasattr(obj, key):
                        setattr(obj, key, value)
                
                # Set updated_at manually to ensure it's updated
                if hasattr(obj, 'updated_at'):
                    from datetime import datetime, UTC
                    obj.updated_at = datetime.now(UTC)
                
                self.db.commit()
                self.db.refresh(obj)
                logger.info(f"Successfully updated {self.model.__name__} with ID: {id}")
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Database error updating {self.model.__name__} ID {id}: {str(e)}")
                raise
        return obj
