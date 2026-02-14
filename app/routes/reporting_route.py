from datetime import date
from typing import List, Optional, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies.reporting_dependencies import get_reporting_service
from app.dependencies.user_dependencies import get_current_user, get_user_base_currency
from app.entities.user import User
from app.schemas.base_schemas import SearchResponse
from app.schemas.reporting_schemas import (
    BalanceAccountsResponse,
    BalanceHistoryResponse,
    BalanceResponse,
    CashflowHistoryParameters,
    CashflowHistoryResponse,
    CashflowSummaryResponse,
    CategorySummaryResponse,
    ReportingParameters,
    TransactionSummaryPeriod,
)
from app.services.reporting_service import ReportingService

router = APIRouter()


@router.get(
    "/categories-summary", response_model=SearchResponse[CategorySummaryResponse]
)
def get_categories_summary(
    parameters: ReportingParameters = Depends(),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[CategorySummaryResponse]:
    """
    Get categories with their transaction amounts for a specified period or date range.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`

    Date range: Provide EITHER `period` OR both `date_from` and `date_to`.
    If `period` is set, date filters are ignored.

    Query parameters:
    - `period` (optional): Time period for aggregation. Options: `day`, `week`, `month`, `year`
    - `date_from` (optional): Start date (use with `date_to`, ignored when `period` is set)
    - `date_to` (optional): End date (use with `date_from`, ignored when `period` is set)
    - `type` (optional): Filter categories by type (`income` or `expense`)
    - `category_id` (optional): Filter to a single category
    - `account_id` (optional): Filter transactions by account
    - `transaction_type` (optional): Filter transactions by type (`income` or `expense`)
    - `currency` (optional): Filter by currency
    - `amount_min` (optional): Minimum transaction amount
    - `amount_max` (optional): Maximum transaction amount
    - `source` (optional): Filter by transaction source
    - `full_list` (optional, default true): If true, return all categories including those with 0 transactions. If false, return only categories that have matching transactions.

    Returns categories with a `transaction_amount` field containing the net-signed sum
    (income adds, expense subtracts) for the specified period.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_categories_summary(user_id=user_id, parameters=parameters)


@router.get("/cashflow-summary", response_model=CashflowSummaryResponse)
def get_cashflow_summary(
    parameters: ReportingParameters = Depends(),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
) -> CashflowSummaryResponse:
    """
    Get income, expense, and total (net cashflow) for a period or date range.

    Reuses the same query parameters as categories-summary:
    - `period` or `date_from`/`date_to`
    - `type`, `category_id`, `account_id`, `currency`, `amount_min`, `amount_max`, `source`
    """
    user_id = cast(UUID, current_user.id)
    return service.get_cashflow_summary(user_id=user_id, parameters=parameters)


@router.get("/cashflow/history", response_model=CashflowHistoryResponse)
def get_cashflow_history(
    parameters: CashflowHistoryParameters = Depends(),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
    base_currency: str = Depends(get_user_base_currency),
) -> CashflowHistoryResponse:
    """Get historical cashflow series by period and date range."""
    user_id = cast(UUID, current_user.id)
    return service.get_cashflow_history_response(
        user_id=user_id,
        parameters=parameters,
        base_currency=base_currency,
    )


# -------------------------------------------------------------------------
# Balance reporting (read-only; never mutates transactions or ledger).
# Balances = projections; FX conversion at read time only.
# -------------------------------------------------------------------------


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    as_of: Optional[date] = Query(
        default=None,
        description="Date as of which to compute balance (default: today)",
    ),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
    base_currency: str = Depends(get_user_base_currency),
) -> BalanceResponse:
    """
    Return the user's total balance as of a date (default: today), converted to the user's base currency.
    Read-only; does not mutate transactions or ledger.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_balance_response(user_id, as_of=as_of, currency=base_currency)


@router.get("/balance/accounts", response_model=BalanceAccountsResponse)
def get_balance_accounts(
    as_of: Optional[date] = Query(
        default=None,
        description="Date as of which to compute balances (default: today)",
    ),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
    base_currency: str = Depends(get_user_base_currency),
) -> BalanceAccountsResponse:
    """
    Return current balance per account as of a date. Includes native and converted (base currency) amounts.
    Read-only; does not mutate transactions or ledger.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_balance_accounts_response(
        user_id, currency=base_currency, as_of=as_of
    )


@router.get("/balance/history", response_model=BalanceHistoryResponse)
def get_balance_history(
    from_date: date = Query(..., alias="from", description="Start date (inclusive)"),
    to_date: date = Query(..., alias="to", description="End date (inclusive)"),
    period: TransactionSummaryPeriod = Query(
        TransactionSummaryPeriod.MONTH,
        description="Granularity: day | week | month | year",
    ),
    account_id: Optional[UUID] = Query(
        default=None, description="Optional: filter by account"
    ),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
    base_currency: str = Depends(get_user_base_currency),
) -> BalanceHistoryResponse:
    """
    Return balance history for charts or lists. Balances are projections (may change with FX revaluation).
    Does not scan full transaction history per point; uses snapshots efficiently.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_balance_history_response(
        user_id,
        from_date=from_date,
        to_date=to_date,
        currency=base_currency,
        period=period,
        account_id=account_id,
    )
