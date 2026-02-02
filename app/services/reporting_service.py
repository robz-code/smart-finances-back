import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException

from app.entities.balance_snapshot import BalanceSnapshot
from app.entities.category import Category, CategoryType
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.schemas.base_schemas import SearchResponse
from app.schemas.reporting_schemas import (
    AccountBalanceItem,
    BalanceAccountsResponse,
    BalanceHistoryPoint,
    BalanceHistoryResponse,
    BALANCE_HISTORY_PERIODS,
    BalanceResponse,
    CashflowSummaryResponse,
    CategoryAggregationData,
    CategorySummaryResponse,
    ReportingParameters,
    TransactionSummaryPeriod,
)
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.fx_service import FxService
from app.services.transaction_service import TransactionService
from app.shared.helpers.date_helper import calculate_period_dates, first_day_of_month


logger = logging.getLogger(__name__)


class ReportingService:
    """
    Service for cross-domain reporting and aggregation.

    This service orchestrates data from multiple domain services to provide
    aggregated reports without creating circular dependencies.

    Balance reporting: Balances are projections (reporting), derived from
    transactions + snapshots. They are never stored as truth. FX conversion
    is a presentation concern at read time only.
    """

    def __init__(
        self,
        category_service: CategoryService,
        transaction_service: TransactionService,
        account_service: AccountService,
        balance_snapshot_repository: BalanceSnapshotRepository,
        fx_service: FxService,
    ):
        self.category_service = category_service
        self.transaction_service = transaction_service
        self.account_service = account_service
        self.balance_snapshot_repository = balance_snapshot_repository
        self.fx_service = fx_service

    def get_categories_summary(
        self,
        user_id: UUID,
        parameters: ReportingParameters,
    ) -> SearchResponse[CategorySummaryResponse]:
        """
        Get categories with their transaction amounts for a given period or date range.

        Uses period (day/week/month/year) OR date_from/date_to. Period takes precedence.
        Applies all optional filters from parameters: account_id, category_id, category_type,
        transaction_type, currency, amount_min, amount_max, source.

        Args:
            user_id: User ID to filter categories and transactions
            parameters: Reporting parameters including date range and optional filters

        Returns:
            SearchResponse containing CategorySummaryResponse objects with transaction amounts
        """
        # 1. Resolve date range: period takes precedence over date_from/date_to
        if parameters.period is not None:
            date_from, date_to = calculate_period_dates(parameters.period)
        else:
            date_from = parameters.date_from
            date_to = parameters.date_to
            assert date_from is not None and date_to is not None  # validated by schema

        # 2. Fetch categories via CategoryService
        if parameters.type is not None:
            categories_response = self.category_service.get_by_user_id_and_type(
                user_id, CategoryType(parameters.type)
            )
        else:
            categories_response = self.category_service.get_by_user_id(user_id)

        categories: List[Category] = categories_response.results

        # If category_id filter is set, restrict to that single category
        if parameters.category_id is not None:
            categories = [c for c in categories if c.id == parameters.category_id]
            if not categories:
                return SearchResponse(total=0, results=[])

        # 3. Get aggregated transaction amounts and counts via TransactionService (single query)
        category_ids = [cat.id for cat in categories]
        amounts_and_counts_by_category = (
            self.transaction_service.get_net_signed_amounts_and_counts_by_category(
                user_id=user_id,
                date_from=date_from,
                date_to=date_to,
                category_ids=category_ids if category_ids else None,
                account_id=parameters.account_id,
                currency=parameters.currency,
                amount_min=parameters.amount_min,
                amount_max=parameters.amount_max,
                source=parameters.source,
            )
        )

        # 4. Merge and return enriched response
        category_summaries = []
        for cat in categories:
            aggregation_data = amounts_and_counts_by_category.get(
                cat.id,
                CategoryAggregationData(
                    net_signed_amount=Decimal("0"), transaction_count=0
                ),
            )
            # When full_list is False, skip categories with no transactions
            if not parameters.full_list and cat.id not in amounts_and_counts_by_category:
                continue
            category_summaries.append(
                CategorySummaryResponse(
                    id=cat.id,
                    name=cat.name,
                    type=CategoryType(cat.type),
                    icon=cat.icon,
                    color=cat.color,
                    transaction_amount=aggregation_data.net_signed_amount,
                    transaction_count=aggregation_data.transaction_count,
                )
            )

        return SearchResponse(total=len(category_summaries), results=category_summaries)

    def get_cashflow_summary(
        self,
        user_id: UUID,
        parameters: ReportingParameters,
    ) -> CashflowSummaryResponse:
        """
        Get income, expense, and total for a period or date range.
        Reuses the same filters as categories-summary.
        """
        if parameters.period is not None:
            date_from, date_to = calculate_period_dates(parameters.period)
        else:
            date_from = parameters.date_from
            date_to = parameters.date_to
            assert date_from is not None and date_to is not None

        category_ids: Optional[List[UUID]] = None
        if parameters.type is not None or parameters.category_id is not None:
            if parameters.type is not None:
                categories_response = self.category_service.get_by_user_id_and_type(
                    user_id, CategoryType(parameters.type)
                )
            else:
                categories_response = self.category_service.get_by_user_id(user_id)
            categories = categories_response.results
            if parameters.category_id is not None:
                categories = [c for c in categories if c.id == parameters.category_id]
            category_ids = [c.id for c in categories] if categories else []

        income, expense, total = self.transaction_service.get_cashflow_summary(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            category_ids=category_ids if category_ids else None,
            account_id=parameters.account_id,
            currency=parameters.currency,
            amount_min=parameters.amount_min,
            amount_max=parameters.amount_max,
            source=parameters.source,
        )
        return CashflowSummaryResponse(income=income, expense=expense, total=total)

    # -------------------------------------------------------------------------
    # Balance reporting (read-only; never mutates transactions or ledger).
    # Balances = projections derived from transactions + snapshots.
    # FX conversion = presentation at read time only; uses as_of date.
    # -------------------------------------------------------------------------

    def get_account_balance(
        self, account_id: UUID, as_of: date
    ) -> tuple[Decimal, str]:
        """
        Compute native balance for one account as of a date.

        Uses snapshots + transactions. If no snapshot exists for the month,
        computes balance at start of month and stores it lazily (snapshots are
        rebuildable). Snapshot represents balance at start of snapshot_date;
        transactions included when snapshot_date < transaction_date <= as_of.
        """
        account = self.account_service.get(account_id)
        currency = account.currency
        initial = Decimal(str(account.initial_balance or 0))

        month_start = first_day_of_month(as_of)
        snap = self.balance_snapshot_repository.get_latest_before_or_on(
            account_id, as_of
        )

        logger.debug(f"Starting snapshot lookup for account {account_id} as of {as_of}")

        if snap:
            # Balance at as_of = snapshot balance + net transactions (snap_date, as_of]
            base = Decimal(str(snap.balance))
            snap_date = snap.snapshot_date
            day_after_snap = snap_date + timedelta(days=1)
            delta = self.transaction_service.get_net_signed_sum_for_account(
                account_id, day_after_snap, as_of
            )
            return (base + delta, currency)
        else:
            # No snapshot: compute balance at start of month_start, lazy-create snapshot
            # Balance at start of month = initial_balance + sum(transactions with date < month_start)
            oldest = date(1900, 1, 1)
            day_before_month = month_start - timedelta(days=1)
            sum_before = self.transaction_service.get_net_signed_sum_for_account(
                account_id, oldest, day_before_month
            )
            balance_at_month_start = initial + sum_before

            # Lazy-create snapshot (avoid duplicate: check again)
            existing = self.balance_snapshot_repository.get_by_account_and_date(
                account_id, month_start
            )
            if not existing:
                snapshot = BalanceSnapshot(
                    account_id=account_id,
                    currency=currency,
                    snapshot_date=month_start,
                    balance=balance_at_month_start,
                )
                self.balance_snapshot_repository.add(snapshot)
                logger.debug(f"Created snapshot for account {account_id} at {month_start} with balance {balance_at_month_start}")

            # Add net transactions from month_start through as_of (inclusive)
            delta = self.transaction_service.get_net_signed_sum_for_account(
                account_id, month_start, as_of
            )
            return (balance_at_month_start + delta, currency)

    def get_accounts_balance(
        self, user_id: UUID, as_of: date, base_currency: str
    ) -> tuple[List[dict], Decimal]:
        """
        Balance per account as of a date, converted to base currency.
        Returns (list of account balance dicts, total).
        """
        accounts_response = self.account_service.get_by_user_id(user_id)
        active = [a for a in accounts_response.results if not getattr(a, "is_deleted", False)]
        accounts_list: List[dict] = []
        total_converted = Decimal("0")
        for acc in active:
            balance_native, currency = self.get_account_balance(acc.id, as_of)
            balance_converted = self.fx_service.convert(
                balance_native, currency, base_currency, as_of
            )
            total_converted += balance_converted
            accounts_list.append({
                "account_id": acc.id,
                "account_name": acc.name,
                "currency": currency,
                "balance_native": balance_native,
                "balance_converted": balance_converted,
            })
        return (accounts_list, total_converted)

    def get_balance_response(
        self,
        user_id: UUID,
        currency: str,
        as_of: Optional[date] = None
    ) -> BalanceResponse:
        """
        Return total balance as of a date (default: today) in base currency.
        Handles default resolution and response building.
        """
        as_of_date = as_of or date.today()
        _, total = self.get_accounts_balance(user_id, as_of_date, currency)
        return BalanceResponse(as_of=as_of_date, currency=currency, balance=total)

    def get_balance_accounts_response(
        self,
        user_id: UUID,
        currency: str,
        as_of: Optional[date] = None
    ) -> BalanceAccountsResponse:
        """
        Return balance per account as of a date. Includes native and converted amounts.
        Handles default resolution and response building.
        """
        as_of_date = as_of or date.today()
        accounts_list, total = self.get_accounts_balance(user_id, as_of_date, currency)
        items = [AccountBalanceItem(**a) for a in accounts_list]
        return BalanceAccountsResponse(
            as_of=as_of_date, currency=currency, accounts=items, total=total
        )

    def get_balance_history_response(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        currency: str,
        period: TransactionSummaryPeriod = TransactionSummaryPeriod.DAY,
        account_id: Optional[UUID] = None
    ) -> BalanceHistoryResponse:
        """
        Return balance history for charts or lists. Validates inputs and builds response.
        Supports day, week, month only (year is not supported for balance history).
        """
        if from_date > to_date:
            raise HTTPException(
                status_code=422, detail="'from' must be before or equal to 'to'"
            )
        if period not in BALANCE_HISTORY_PERIODS:
            raise HTTPException(
                status_code=422,
                detail="period must be one of: day, week, month (year not supported)",
            )
        period_str = period.value
        points_data = self.get_balance_history(
            user_id, from_date, to_date, period_str, account_id, currency
        )
        points = [
            BalanceHistoryPoint(date=p["date"], balance=p["balance"])
            for p in points_data
        ]
        return BalanceHistoryResponse(
            currency=currency, period=period_str, points=points
        )

    def get_balance_history(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        period: str,
        account_id: Optional[UUID],
        base_currency: str,
    ) -> List[dict]:
        """
        Balance history for charts/lists. Uses snapshots efficiently; does not
        scan full transaction history per point. History is a projection (may
        change with FX revaluation).
        """
        points: List[dict] = []
        if period == "day":
            current = from_date
            while current <= to_date:
                if account_id:
                    bal, _ = self.get_account_balance(account_id, current)
                    converted = self.fx_service.convert(
                        bal, _, base_currency, current
                    )
                else:
                    converted = self.get_total_balance(user_id, current, base_currency)
                points.append({"date": current.isoformat(), "balance": converted})
                current += timedelta(days=1)
        elif period == "week":
            current = from_date
            while current <= to_date:
                if account_id:
                    bal, _ = self.get_account_balance(account_id, current)
                    converted = self.fx_service.convert(
                        bal, _, base_currency, current
                    )
                else:
                    converted = self.get_total_balance(user_id, current, base_currency)
                points.append({"date": current.isoformat(), "balance": converted})
                current += timedelta(days=7)
        else:  # month
            # First day of each month in range
            year, month = from_date.year, from_date.month
            end_y, end_m = to_date.year, to_date.month
            while (year, month) <= (end_y, end_m):
                d = date(year, month, 1)
                if d > to_date:
                    break
                if account_id:
                    bal, _ = self.get_account_balance(account_id, d)
                    converted = self.fx_service.convert(
                        bal, _, base_currency, d
                    )
                else:
                    converted = self.get_total_balance(user_id, d, base_currency)
                points.append({"date": d.isoformat(), "balance": converted})
                if month == 12:
                    year, month = year + 1, 1
                else:
                    month += 1
        return points
