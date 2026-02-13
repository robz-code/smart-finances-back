import logging
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Integer, case, cast, func, literal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.entities.tag import Tag
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
        logger.debug(f"DB search: Transaction user_id={user_id}")
        query = (
            self.db.query(Transaction)
            .options(
                selectinload(Transaction.account),
                selectinload(Transaction.category),
                selectinload(Transaction.concept),
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

    def attach_tags(self, transaction: Transaction, tags: List[Tag]) -> None:
        """Persist the relationship between a transaction and multiple tags."""
        logger.debug(
            f"DB attach_tags: Transaction id={transaction.id} tags_count={len(tags)}"
        )
        try:
            for tag in tags:
                # Check if association already exists to avoid duplicates
                existing = (
                    self.db.query(TransactionTag)
                    .filter(
                        TransactionTag.transaction_id == transaction.id,
                        TransactionTag.tag_id == tag.id,
                    )
                    .first()
                )
                if not existing:
                    association = TransactionTag(
                        transaction_id=transaction.id, tag_id=tag.id
                    )
                    self.db.add(association)
            self.db.commit()
            self.db.refresh(transaction)
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error(
                "Error linking tags to transaction %s: %s",
                transaction.id,
                exc,
            )
            raise HTTPException(
                status_code=500, detail="Error linking tags to transaction"
            ) from exc

    def remove_all_tags(self, transaction_id: UUID) -> int:
        """Delete all tag associations for the given transaction."""
        logger.debug(f"DB remove_all_tags: transaction_id={transaction_id}")
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

    def get_net_signed_amounts_and_counts_by_category(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        category_ids: Optional[List[UUID]] = None,
        *,
        account_id: Optional[UUID] = None,
        currency: Optional[str] = None,
        amount_min: Optional[Decimal] = None,
        amount_max: Optional[Decimal] = None,
        source: Optional[str] = None,
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
            account_id: Optional filter by account
            currency: Optional filter by currency
            amount_min: Optional minimum amount
            amount_max: Optional maximum amount
            source: Optional filter by source

        Returns:
            Dictionary mapping category_id to CategoryAggregationData DTO
        """
        logger.debug(
            f"DB get_net_signed_amounts_and_counts_by_category: user_id={user_id} "
            f"date_from={date_from} date_to={date_to}"
        )
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
        if account_id is not None:
            query = query.filter(Transaction.account_id == account_id)
        if currency is not None:
            query = query.filter(Transaction.currency == currency)
        if amount_min is not None:
            query = query.filter(Transaction.amount >= amount_min)
        if amount_max is not None:
            query = query.filter(Transaction.amount <= amount_max)
        if source is not None:
            query = query.filter(Transaction.source == source)

        results = query.all()

        # Convert to dictionary with DTOs, defaulting to (Decimal('0'), 0) for categories with no transactions
        return {
            category_id: CategoryAggregationData(
                net_signed_amount=(
                    Decimal(str(net_amount)) if net_amount is not None else Decimal("0")
                ),
                transaction_count=int(count) if count is not None else 0,
            )
            for category_id, net_amount, count in results
        }

    def get_cashflow_summary(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        category_ids: Optional[List[UUID]] = None,
        *,
        account_id: Optional[UUID] = None,
        currency: Optional[str] = None,
        amount_min: Optional[Decimal] = None,
        amount_max: Optional[Decimal] = None,
        source: Optional[str] = None,
    ) -> tuple[Decimal, Decimal, Decimal]:
        """
        Get income, expense, and total (income - expense) for a date range.

        Uses the same filters as get_net_signed_amounts_and_counts_by_category.
        Returns (income, expense, total).
        """
        logger.debug(
            f"DB get_cashflow_summary: user_id={user_id} date_from={date_from} date_to={date_to}"
        )
        income_expr = case(
            (Transaction.type == TransactionType.INCOME.value, Transaction.amount),
            else_=0,
        )
        expense_expr = case(
            (Transaction.type == TransactionType.EXPENSE.value, Transaction.amount),
            else_=0,
        )

        query = self.db.query(
            func.coalesce(func.sum(income_expr), 0).label("income"),
            func.coalesce(func.sum(expense_expr), 0).label("expense"),
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )

        if category_ids is not None:
            query = query.filter(Transaction.category_id.in_(category_ids))
        if account_id is not None:
            query = query.filter(Transaction.account_id == account_id)
        if currency is not None:
            query = query.filter(Transaction.currency == currency)
        if amount_min is not None:
            query = query.filter(Transaction.amount >= amount_min)
        if amount_max is not None:
            query = query.filter(Transaction.amount <= amount_max)
        if source is not None:
            query = query.filter(Transaction.source == source)

        row = query.first()
        income = Decimal(str(row.income)) if row and row.income else Decimal("0")
        expense = Decimal(str(row.expense)) if row and row.expense else Decimal("0")
        total = income - expense
        return (income, expense, total)

    def _build_period_start_expr(self, period: str):
        """Build DB-specific period bucket expression."""
        dialect = self.db.bind.dialect.name if self.db.bind else ""
        if dialect == "sqlite":
            if period == "day":
                return func.date(Transaction.date)
            if period == "week":
                # SQLite strftime('%w'): Sunday=0..Saturday=6. Normalize to Monday start.
                weekday = cast(func.strftime("%w", Transaction.date), Integer)
                days_since_monday = (weekday + 6) % 7
                return func.date(
                    Transaction.date, func.printf("-%d days", days_since_monday)
                )
            if period == "month":
                return func.strftime("%Y-%m-01", Transaction.date)
            if period == "year":
                return func.strftime("%Y-01-01", Transaction.date)
        else:
            if period == "day":
                return func.date_trunc("day", Transaction.date)
            if period == "week":
                return func.date_trunc("week", Transaction.date)
            if period == "month":
                return func.date_trunc("month", Transaction.date)
            if period == "year":
                return func.date_trunc("year", Transaction.date)
        raise ValueError(f"Unsupported period '{period}'")

    def get_cashflow_history_grouped(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        period: str,
        *,
        account_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        currency: Optional[str] = None,
        amount_min: Optional[Decimal] = None,
        amount_max: Optional[Decimal] = None,
        source: Optional[str] = None,
    ) -> List[dict]:
        """
        Aggregate historical cashflow rows grouped by period.

        If currency is provided, rows are grouped only by period and currency is returned
        as a constant. Otherwise rows are grouped by period and transaction currency.
        """
        period_start_expr = self._build_period_start_expr(period).label("period_start")
        income_expr = case(
            (Transaction.type == TransactionType.INCOME.value, Transaction.amount),
            else_=0,
        )
        expense_expr = case(
            (Transaction.type == TransactionType.EXPENSE.value, Transaction.amount),
            else_=0,
        )

        if currency is not None:
            query = self.db.query(
                period_start_expr,
                literal(currency).label("currency"),
                func.coalesce(func.sum(income_expr), 0).label("income"),
                func.coalesce(func.sum(expense_expr), 0).label("expense_abs"),
            ).group_by(period_start_expr)
        else:
            query = self.db.query(
                period_start_expr,
                Transaction.currency.label("currency"),
                func.coalesce(func.sum(income_expr), 0).label("income"),
                func.coalesce(func.sum(expense_expr), 0).label("expense_abs"),
            ).group_by(period_start_expr, Transaction.currency)

        query = query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )

        if account_id is not None:
            query = query.filter(Transaction.account_id == account_id)
        if category_id is not None:
            query = query.filter(Transaction.category_id == category_id)
        if currency is not None:
            query = query.filter(Transaction.currency == currency)
        if amount_min is not None:
            query = query.filter(Transaction.amount >= amount_min)
        if amount_max is not None:
            query = query.filter(Transaction.amount <= amount_max)
        if source is not None:
            query = query.filter(Transaction.source == source)

        query = query.order_by(period_start_expr.asc())
        rows = query.all()
        return [
            {
                "period_start": r.period_start,
                "currency": r.currency,
                "income": Decimal(str(r.income)) if r.income is not None else Decimal("0"),
                "expense_abs": (
                    Decimal(str(r.expense_abs))
                    if r.expense_abs is not None
                    else Decimal("0")
                ),
            }
            for r in rows
        ]

    def get_transactions_for_accounts_until_date(
        self, account_ids: List[UUID], to_date_inclusive: date
    ) -> List[tuple]:
        """
        Get all transactions for given accounts with date <= to_date_inclusive.
        Returns list of (account_id, transaction_date, signed_amount).
        signed_amount: income=+amount, expense=-amount.
        """
        if not account_ids:
            return []
        logger.debug(
            f"DB get_transactions_for_accounts_until_date: account_ids={len(account_ids)} "
            f"to_date={to_date_inclusive}"
        )
        net_amount = case(
            (Transaction.type == TransactionType.INCOME.value, Transaction.amount),
            else_=-Transaction.amount,
        )
        rows = (
            self.db.query(
                Transaction.account_id,
                Transaction.date,
                net_amount.label("signed_amount"),
            )
            .filter(
                Transaction.account_id.in_(account_ids),
                Transaction.date <= to_date_inclusive,
            )
            .all()
        )
        return [(r.account_id, r.date, Decimal(str(r.signed_amount))) for r in rows]

    def get_transactions_for_accounts_in_range(
        self,
        account_ids: List[UUID],
        from_date: date,
        to_date: date,
    ) -> List[tuple]:
        """
        Get transactions for accounts in [from_date, to_date] inclusive.
        Returns list of (account_id, transaction_date, signed_amount).
        """
        if not account_ids:
            return []
        logger.debug(
            f"DB get_transactions_for_accounts_in_range: account_ids={len(account_ids)} "
            f"from={from_date} to={to_date}"
        )
        net_amount = case(
            (Transaction.type == TransactionType.INCOME.value, Transaction.amount),
            else_=-Transaction.amount,
        )
        rows = (
            self.db.query(
                Transaction.account_id,
                Transaction.date,
                net_amount.label("signed_amount"),
            )
            .filter(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= from_date,
                Transaction.date <= to_date,
            )
            .order_by(Transaction.date)
            .all()
        )
        return [(r.account_id, r.date, Decimal(str(r.signed_amount))) for r in rows]

    def get_net_signed_sum_for_account(
        self, account_id: UUID, date_from: date, date_to: date
    ) -> Decimal:
        """
        Net-signed sum of transactions for one account in [date_from, date_to] (inclusive).

        Used for balance reporting: income adds, expense subtracts.
        Transactions = ledger (facts); this is read-only aggregation for reporting.
        """
        logger.debug(
            f"DB get_net_signed_sum_for_account: account_id={account_id} "
            f"date_from={date_from} date_to={date_to}"
        )
        net_amount = case(
            (Transaction.type == TransactionType.INCOME.value, Transaction.amount),
            else_=-Transaction.amount,
        )
        row = (
            self.db.query(func.coalesce(func.sum(net_amount), 0).label("net"))
            .filter(
                Transaction.account_id == account_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .first()
        )
        return Decimal(str(row.net)) if row and row.net is not None else Decimal("0")
