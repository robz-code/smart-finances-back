from uuid import UUID
from fastapi import HTTPException
from typing import List, Optional, Any

class BaseService:
    def __init__(self, db):
        self.db = db
        self.repository = None

    def get_all(self) -> List[Any]:
        """Get all objects"""
        return self.repository.get_all()

    def get(self, id: UUID) -> Any:
        """Get object by ID with error handling"""
        obj = self.repository.get(id) 
        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")
        return obj

    def get_by_user_id(self, user_id: UUID) -> List[Any]:
        """Get objects by user ID"""
        return self.repository.get_by_user_id(user_id)

    def delete(self, id: UUID) -> Any:
        """Delete object by ID with error handling"""
        obj = self.repository.get(id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")
        
        deleted_obj = self.repository.delete(id)
        return deleted_obj

    def add(self, obj_in: Any) -> Any:
        """Add new object"""
        return self.repository.add(obj_in)

    def update(self, id: UUID, obj_in: Any) -> Any:
        """Update object by ID with error handling"""
        obj = self.repository.get(id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")
        
        return self.repository.update(id, obj_in)
