from app.repository.base_repository import BaseRepository
from app.entities.user_debt import UserDebt
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

class DebtRepository(BaseRepository[UserDebt]):
    def __init__(self, db: Session):
        super().__init__(db, UserDebt)

    def get_user_debts(self, user_id: UUID, contact_id: UUID) -> List:
        """Get all debts between two users"""
        debts = self.db.query(UserDebt).filter(
            ((UserDebt.from_user_id == user_id) & (UserDebt.to_user_id == contact_id)) |
            ((UserDebt.from_user_id == contact_id) & (UserDebt.to_user_id == user_id))
        ).all()
        
        return debts