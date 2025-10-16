from typing import List
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.entities.transaction import Transaction
from app.entities.transaction_tag import TransactionTag
from app.repository.base_repository import BaseRepository
from app.schemas.transaction_schemas import TransactionSearch


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: Session):
        super().__init__(db, Transaction)

    def search(
        self, user_id: UUID, search_params: TransactionSearch
    ) -> List[Transaction]:
        """Search transactions based on various criteria"""
        query = (
            self.db.query(Transaction)
            .options(
                selectinload(Transaction.account),
                selectinload(Transaction.category),
                selectinload(Transaction.group),
                selectinload(Transaction.installments),
                selectinload(Transaction.transaction_tags).selectinload(
                    TransactionTag.tag
                ),
            )
            .filter(Transaction.user_id == user_id)
        )

        for filter_condition in search_params.build_filters():
            query = query.filter(filter_condition)

        # Order by date descending (most recent first)
        query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())

        return query.all()

    def get_by_account_id(self, user_id: UUID, account_id: UUID) -> List[Transaction]:
        """Get transactions by account ID for a specific user"""
        return (
            self.db.query(Transaction)
            .options(
                selectinload(Transaction.account),
                selectinload(Transaction.category),
                selectinload(Transaction.group),
                selectinload(Transaction.installments),
                selectinload(Transaction.transaction_tags).selectinload(
                    TransactionTag.tag
                ),
            )
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
            .options(
                selectinload(Transaction.account),
                selectinload(Transaction.category),
                selectinload(Transaction.group),
                selectinload(Transaction.installments),
                selectinload(Transaction.transaction_tags).selectinload(
                    TransactionTag.tag
                ),
            )
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
            .options(
                selectinload(Transaction.account),
                selectinload(Transaction.category),
                selectinload(Transaction.group),
                selectinload(Transaction.installments),
                selectinload(Transaction.transaction_tags).selectinload(
                    TransactionTag.tag
                ),
            )
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
            .options(
                selectinload(Transaction.account),
                selectinload(Transaction.category),
                selectinload(Transaction.group),
                selectinload(Transaction.installments),
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .all()
        )
