from typing import List, cast
from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.user_debt import UserDebt
from app.repository.debt_repository import DebtRepository
from app.services.base_service import BaseService


class DebtService(BaseService[UserDebt]):
    def __init__(self, db: Session) -> None:
        repository = DebtRepository(db)
        super().__init__(db, repository, UserDebt)

    def get_user_debts(self, user_id: UUID, contact_id: UUID) -> List[UserDebt]:
        """Get all debts between two users"""
        result = self.repository.get_user_debts(user_id, contact_id)
        return cast(List[UserDebt], result)
