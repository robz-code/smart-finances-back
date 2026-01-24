from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.category import Category
from app.repository.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Category)

    def get_transfer_category(self, user_id: UUID) -> Category:
        return (
            self.db.query(self.model)
            .filter(self.model.user_id == user_id, self.model.name == "transfer")
            .first()
        )

    def get_by_user_id_and_type(
        self, user_id: UUID, category_type: str
    ) -> List[Category]:
        return (
            self.db.query(self.model)
            .filter(self.model.user_id == user_id, self.model.type == category_type)
            .all()
        )
