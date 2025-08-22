from sqlalchemy.orm import Session

from app.entities.category import Category
from app.repository.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Category)
