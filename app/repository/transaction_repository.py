import logging
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import case, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.entities.tags import Tag
from app.entities.transaction import Transaction, TransactionType
from app.entities.transaction_tag import TransactionTag
from app.repository.base_repository import BaseRepository
from app.schemas.reporting_schemas import CategoryAggregationData
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

    def get_tag_association(self, transaction_id: UUID) -> Optional[TransactionTag]:
        """Return the first tag association for the given transaction."""
        return (
            self.db.query(TransactionTag)
            .options(selectinload(TransactionTag.tag))
            .filter(TransactionTag.transaction_id == transaction_id)
            .first()
        )

    def remove_tags(self, transaction_id: UUID) -> int:
        """Delete all tag associations for the given transaction."""
        try:
            deleted = (
                self.db.query(TransactionTag)
                .filter(TransactionTag.transaction_id == transaction_id)
                .delete(synchronize_session=False)
            )
            if deleted:
                logger.info(
                    "Removed %s tag associations for transaction %s",
                    deleted,
                    transaction_id,
                )
            self.db.commit()
            return deleted
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error(
                "Error removing tag associations for transaction %s: %s",
                transaction_id,
                exc,
            )
            raise HTTPException(
                status_code=500, detail="Error removing transaction tags"
            ) from exc

    def get_net_signed_amounts_by_category(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        category_ids: Optional[List[UUID]] = None,
    ) -> Dict[UUID, Decimal]:
        """
        Get net-signed transaction amounts grouped by category_id.
        
        Net-signed means: income transactions add to the total, expense transactions subtract.
        Formula: sum(case when type='income' then amount else -amount end)
        
        Args:
            user_id: User ID to filter transactions
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            category_ids: Optional list of category IDs to filter by. If None, includes all categories.
        
        Returns:
            Dictionary mapping category_id to net-signed Decimal amount
        """
        # Build the CASE expression for net-signed calculation
        # Income adds (positive), expense subtracts (negative)
        net_amount = case(
            (Transaction.type == TransactionType.INCOME.value, Transaction.amount),
            else_=-Transaction.amount,
        )

        query = (
            self.db.query(
                Transaction.category_id,
                func.sum(net_amount).label("net_amount"),
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .group_by(Transaction.category_id)
        )

        if category_ids is not None:
            query = query.filter(Transaction.category_id.in_(category_ids))

        results = query.all()

        # Convert to dictionary, defaulting to Decimal('0') for categories with no transactions
        return {
            category_id: Decimal(str(net_amount)) if net_amount is not None else Decimal("0")
            for category_id, net_amount in results
        }

    def get_net_signed_amounts_and_counts_by_category(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        category_ids: Optional[List[UUID]] = None,
    ) -> Dict[UUID, CategoryAggregationData]:
        """
        Get net-signed transaction amounts and counts grouped by category_id in a single query.
        
        Net-signed means: income transactions add to the total, expense transactions subtract.
        This method combines both amount and count calculations in one database query for efficiency.
        
        Args:
            user_id: User ID to filter transactions
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            category_ids: Optional list of category IDs to filter by. If None, includes all categories.
        
        Returns:
            Dictionary mapping category_id to CategoryAggregationData DTO
        """
        # Build the CASE expression for net-signed calculation
        # Income adds (positive), expense subtracts (negative)
        net_amount = case(
            (Transaction.type == TransactionType.INCOME.value, Transaction.amount),
            else_=-Transaction.amount,
        )

        query = (
            self.db.query(
                Transaction.category_id,
                func.sum(net_amount).label("net_amount"),
                func.count(Transaction.id).label("count"),
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .group_by(Transaction.category_id)
        )

        if category_ids is not None:
            query = query.filter(Transaction.category_id.in_(category_ids))

        results = query.all()

        # Convert to dictionary with DTOs, defaulting to (Decimal('0'), 0) for categories with no transactions
        return {
            category_id: CategoryAggregationData(
                net_signed_amount=Decimal(str(net_amount)) if net_amount is not None else Decimal("0"),
                transaction_count=int(count) if count is not None else 0,
            )
            for category_id, net_amount, count in results
        }
