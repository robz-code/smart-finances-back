from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.transaction import Transaction
from app.repository.base_repository import BaseRepository
from app.schemas.transaction_schemas import TransactionSearch


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: Session):
        super().__init__(db, Transaction)

    def search(
        self, user_id: UUID, search_params: TransactionSearch
    ) -> List[Transaction]:
        """Search transactions based on various criteria"""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)

        if search_params.account_id:
            query = query.filter(Transaction.account_id == search_params.account_id)

        if search_params.category_id:
            query = query.filter(Transaction.category_id == search_params.category_id)

        if search_params.group_id:
            query = query.filter(Transaction.group_id == search_params.group_id)

        if search_params.type:
            query = query.filter(Transaction.type == search_params.type)

        if search_params.currency:
            query = query.filter(Transaction.currency == search_params.currency)

        if search_params.date_from:
            query = query.filter(Transaction.date >= search_params.date_from)

        if search_params.date_to:
            query = query.filter(Transaction.date <= search_params.date_to)

        if search_params.amount_min is not None:
            query = query.filter(Transaction.amount >= search_params.amount_min)

        if search_params.amount_max is not None:
            query = query.filter(Transaction.amount <= search_params.amount_max)

        if search_params.source:
            query = query.filter(Transaction.source == search_params.source)

        if search_params.has_installments is not None:
            query = query.filter(
                Transaction.has_installments == search_params.has_installments
            )

        # Order by date descending (most recent first)
        query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())

        return query.all()

    def get_by_account_id(self, user_id: UUID, account_id: UUID) -> List[Transaction]:
        """Get transactions by account ID for a specific user"""
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id, Transaction.account_id == account_id
            )
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .all()
        )

    def get_by_category_id(self, user_id: UUID, category_id: UUID) -> List[Transaction]:
        """Get transactions by category ID for a specific user"""
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id, Transaction.category_id == category_id
            )
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .all()
        )

    def get_by_group_id(self, user_id: UUID, group_id: UUID) -> List[Transaction]:
        """Get transactions by group ID for a specific user"""
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id, Transaction.group_id == group_id)
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .all()
        )

    def get_by_date_range(
        self, user_id: UUID, date_from: str, date_to: str
    ) -> List[Transaction]:
        """Get transactions within a date range for a specific user"""
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .all()
        )
