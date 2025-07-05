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
            for key, value in obj_in.items():
                setattr(obj, key, value)
            self.db.commit()
            self.db.refresh(obj)
        return obj
