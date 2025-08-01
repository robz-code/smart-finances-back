from sqlalchemy.orm import Session
from uuid import UUID


class BaseRepository():
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model

    def get_all(self):
        return self.db.query(self.model).all()

    def get(self, id: UUID):
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_by_user_id(self, user_id: UUID):
        return self.db.query(self.model).filter(self.model.user_id == user_id).all()

    def delete(self, id: UUID):
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj

    def add(self, obj_in):
        
        self.db.add(obj_in)
        self.db.commit()
        self.db.refresh(obj_in)
        return obj_in
    
    def update(self, id: UUID, obj_in):
        obj = self.get(id)
        if obj:
            # Extract attributes from the model object, excluding private attributes and id
            update_data = {k: v for k, v in obj_in.__dict__.items() 
                         if not k.startswith('_') and k != 'id'}
            
            # Protect audit fields from being modified
            protected_fields = {'created_at', 'updated_at'}
            for field in protected_fields:
                if field in update_data:
                    del update_data[field]
            
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            # Set updated_at manually to ensure it's updated
            if hasattr(obj, 'updated_at'):
                from datetime import datetime, UTC
                obj.updated_at = datetime.now(UTC)
            
            self.db.commit()
            self.db.refresh(obj)
        return obj
