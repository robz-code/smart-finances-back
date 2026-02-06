import logging
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException

from app.entities.category import Category, CategoryType
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
from app.engines.balance.factory import BalanceStrategyFactory
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.shared.helpers.date_helper import calculate_period_dates


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
        balance_strategy_factory: BalanceStrategyFactory,
    ):
        self.category_service = category_service
        self.transaction_service = transaction_service
        self.account_service = account_service
        self.balance_strategy_factory = balance_strategy_factory

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
    # Balance reporting (read-only; strategy-based, O(1) queries).
    # Balances = projections derived from transactions + snapshots.
    # FX conversion = presentation at read time only.
    # -------------------------------------------------------------------------

    def get_balance_response(
        self,
        user_id: UUID,
        currency: str,
        as_of: Optional[date] = None,
    ) -> BalanceResponse:
        """
        Return total balance as of a date (default: today) in base currency.
        Uses TotalBalanceAtDateStrategy (O(1) queries).
        """
        as_of_date = as_of or date.today()
        strategy = self.balance_strategy_factory.create_total_balance_strategy(
            user_id, as_of_date, currency
        )
        total = strategy.execute()
        return BalanceResponse(
            as_of=as_of_date, currency=currency, balance=total
        )

    def get_balance_accounts_response(
        self,
        user_id: UUID,
        currency: str,
        as_of: Optional[date] = None,
    ) -> BalanceAccountsResponse:
        """
        Return balance per account as of a date. Includes native and converted amounts.
        Uses PerAccountBalanceAtDateStrategy (O(1) queries).
        """
        as_of_date = as_of or date.today()
        strategy = self.balance_strategy_factory.create_per_account_balance_strategy(
            user_id, as_of_date, currency
        )
        accounts_list, total = strategy.execute()
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
        account_id: Optional[UUID] = None,
    ) -> BalanceHistoryResponse:
        """
        Return balance history for charts or lists. Validates inputs and builds response.
        Uses BalanceHistoryStrategy (O(1) queries).
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
        strategy = self.balance_strategy_factory.create_balance_history_strategy(
            user_id, from_date, to_date, period_str, currency, account_id
        )
        points_data = strategy.execute()
        points = [
            BalanceHistoryPoint(date=p["date"], balance=p["balance"])
            for p in points_data
        ]
        return BalanceHistoryResponse(
            currency=currency, period=period_str, points=points
        )
