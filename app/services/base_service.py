from uuid import UUID
from fastapi import HTTPException
class BaseService:
    def __init__(self, db):
        self.db = db
        self.repository = None

    def get_all(self):
        return self.repository.get_all()

    def get(self, id: UUID):
        object = self.repository.get(id) 
        if object is None:
            raise HTTPException(status_code=404, detail="Object not found")
        else:
            return object

    def delete(self, id: UUID):
        return self.repository.delete(id)

    def add(self, obj_in):
        return self.repository.add(obj_in)

    def update(self, id: UUID, obj_in):
        return self.repository.update(id, obj_in)
