import logging
from typing import List
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from fastapi import HTTPException

from app.entities.tags import Tag
from app.entities.transaction import Transaction
from app.entities.transaction_tag import TransactionTag
from app.repository.base_repository import BaseRepository
from app.schemas.transaction_schemas import TransactionSearch

logger = logging.getLogger(__name__)


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

    def attach_tag(self, transaction: Transaction, tag: Tag) -> None:
        """Persist the relationship between a transaction and a tag."""
        association = TransactionTag(transaction_id=transaction.id, tag_id=tag.id)
        try:
            self.db.add(association)
            self.db.commit()
            self.db.refresh(transaction)
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error(
                "Error linking tag %s to transaction %s: %s",
                tag.id,
                transaction.id,
                exc,
            )
            raise HTTPException(
                status_code=500, detail="Error linking tag to transaction"
            ) from exc

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
