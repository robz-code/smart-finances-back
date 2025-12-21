from sqlalchemy.orm import Session

from app.entities.budget import Budget
from app.repository.base_repository import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Budget)
