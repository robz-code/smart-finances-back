from app.repository.base_repository import BaseRepository
from sqlalchemy.orm import Session
from app.entities.category import Category


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)