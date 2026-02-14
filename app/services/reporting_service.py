import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException

from app.engines.balance_engine import BalanceEngine
from app.entities.category import Category, CategoryType
from app.schemas.base_schemas import SearchResponse
from app.schemas.reporting_schemas import (
    BALANCE_HISTORY_PERIODS,
    AccountBalanceItem,
    BalanceAccountsResponse,
    BalanceHistoryPoint,
    BalanceHistoryResponse,
    BalanceResponse,
    CashflowHistoryParameters,
    CashflowHistoryPoint,
    CashflowHistoryResponse,
    CashflowSummaryResponse,
    CategoryAggregationData,
    CategorySummaryResponse,
    PeriodComparisonParameters,
    PeriodComparisonResponse,
    PeriodMetrics,
    PeriodComparisonSummary,
    ReportingParameters,
    TransactionSummaryPeriod,
)
from app.services.category_service import CategoryService
from app.services.fx_service import FxService
from app.services.transaction_service import TransactionService
from app.shared.helpers.date_helper import (
    build_period_buckets,
    calculate_period_dates,
    calculate_previous_equivalent_period,
)

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
        balance_engine: BalanceEngine,
        fx_service: FxService,
    ):
        self.category_service = category_service
        self.transaction_service = transaction_service
        self.balance_engine = balance_engine
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
            if (
                not parameters.full_list
                and cat.id not in amounts_and_counts_by_category
            ):
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

    def get_period_comparison(
        self,
        user_id: UUID,
        parameters: PeriodComparisonParameters,
    ) -> PeriodComparisonResponse:
        """
        Compare current period vs previous equivalent period.
        Reuses get_cashflow_summary logic; 2 queries total.
        """
        # 1. Resolve current period
        if parameters.period is not None:
            current_start, current_end = calculate_period_dates(parameters.period)
        else:
            current_start = parameters.date_from
            current_end = parameters.date_to
            assert current_start is not None and current_end is not None

        # 2. Calculate previous equivalent period
        previous_start, previous_end = calculate_previous_equivalent_period(
            current_start, current_end
        )

        # 3. Resolve category_ids (same logic as get_cashflow_summary)
        category_ids: Optional[List[UUID]] = None
        if parameters.category_id is not None:
            categories_response = self.category_service.get_by_user_id(user_id)
            categories = [
                c for c in categories_response.results if c.id == parameters.category_id
            ]
            category_ids = [c.id for c in categories] if categories else []

        # 4. Get metrics for both periods
        filter_kwargs = dict(
            category_ids=category_ids if category_ids else None,
            account_id=parameters.account_id,
            currency=parameters.currency,
            amount_min=parameters.amount_min,
            amount_max=parameters.amount_max,
            source=parameters.source,
        )
        income_curr, expense_curr, total_curr = (
            self.transaction_service.get_cashflow_summary(
                user_id=user_id,
                date_from=current_start,
                date_to=current_end,
                **filter_kwargs,
            )
        )
        income_prev, expense_prev, total_prev = (
            self.transaction_service.get_cashflow_summary(
                user_id=user_id,
                date_from=previous_start,
                date_to=previous_end,
                **filter_kwargs,
            )
        )

        # 5. Build summary
        difference = total_curr - total_prev
        if total_prev == 0:
            percentage_change = None
            percentage_change_available = False
        else:
            percentage_change = (difference / abs(total_prev)) * Decimal("100")
            percentage_change_available = True
        if difference > 0:
            trend = "up"
        elif difference < 0:
            trend = "down"
        else:
            trend = "flat"

        return PeriodComparisonResponse(
            current_period=PeriodMetrics(
                start=current_start,
                end=current_end,
                income=income_curr,
                expense=expense_curr,
                net=total_curr,
            ),
            previous_period=PeriodMetrics(
                start=previous_start,
                end=previous_end,
                income=income_prev,
                expense=expense_prev,
                net=total_prev,
            ),
            summary=PeriodComparisonSummary(
                difference=difference,
                percentage_change=percentage_change,
                percentage_change_available=percentage_change_available,
                trend=trend,
            ),
        )

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
        Uses BalanceEngine (O(1) queries).
        """
        as_of_date = as_of or date.today()
        total = self.balance_engine.get_total_balance(user_id, as_of_date, currency)
        return BalanceResponse(as_of=as_of_date, currency=currency, balance=total)

    def get_balance_accounts_response(
        self,
        user_id: UUID,
        currency: str,
        as_of: Optional[date] = None,
    ) -> BalanceAccountsResponse:
        """
        Return balance per account as of a date. Includes native and converted amounts.
        Uses BalanceEngine (O(1) queries).
        """
        as_of_date = as_of or date.today()
        accounts_list, total = self.balance_engine.get_accounts_balance(
            user_id, as_of_date, currency
        )
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
        Uses BalanceEngine (O(1) queries).
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
        points_data = self.balance_engine.get_balance_history(
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            period=period_str,
            base_currency=currency,
            account_id=account_id,
        )
        points = [
            BalanceHistoryPoint(date=p["date"], balance=p["balance"])
            for p in points_data
        ]
        return BalanceHistoryResponse(
            currency=currency, period=period_str, points=points
        )

    def _normalize_period_start(self, value: object) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError(f"Unsupported period_start type: {type(value)}")

    def get_cashflow_history_response(
        self,
        user_id: UUID,
        parameters: CashflowHistoryParameters,
        base_currency: str,
    ) -> CashflowHistoryResponse:
        if parameters.category_id is not None:
            category = self.category_service.get(parameters.category_id)
            if category.user_id != user_id:
                raise HTTPException(status_code=404, detail="Category not found")

        rows = self.transaction_service.get_cashflow_history_grouped(
            user_id=user_id,
            date_from=parameters.date_from,
            date_to=parameters.date_to,
            period=parameters.period,
            account_id=parameters.account_id,
            category_id=parameters.category_id,
            currency=parameters.currency,
            amount_min=parameters.amount_min,
            amount_max=parameters.amount_max,
            source=parameters.source,
        )

        output_currency = parameters.currency or base_currency
        bucket_dates = build_period_buckets(
            parameters.date_from, parameters.date_to, parameters.period
        )
        aggregates: dict[date, dict[str, Decimal]] = {
            bucket: {"income": Decimal("0"), "expense_abs": Decimal("0")}
            for bucket in bucket_dates
        }

        for row in rows:
            period_start = self._normalize_period_start(row["period_start"])
            if period_start not in aggregates:
                continue

            income = row["income"]
            expense_abs = row["expense_abs"]

            if parameters.currency is None:
                from_currency = row["currency"] or output_currency
                income = self.fx_service.convert(
                    income, from_currency, output_currency, period_start
                )
                expense_abs = self.fx_service.convert(
                    expense_abs, from_currency, output_currency, period_start
                )

            aggregates[period_start]["income"] += income
            aggregates[period_start]["expense_abs"] += expense_abs

        points: list[CashflowHistoryPoint] = []
        for bucket in sorted(aggregates):
            income = aggregates[bucket]["income"]
            expense = -aggregates[bucket]["expense_abs"]
            net = income + expense
            points.append(
                CashflowHistoryPoint(
                    period_start=bucket.isoformat(),
                    income=income,
                    expense=expense,
                    net=net,
                )
            )

        return CashflowHistoryResponse(
            period=parameters.period.value,
            date_from=parameters.date_from,
            date_to=parameters.date_to,
            currency=output_currency,
            points=points,
        )
