from sqlalchemy.orm import Session

from app.entities.category import Category
from app.repository.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Category)

    def get_transfer_category(self, user_id: str) -> Category:
        
        return self.db.query(self.model).filter(
            self.model.user_id == user_id and 
            self.model.type == "transfer").first()
