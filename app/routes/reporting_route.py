from datetime import date
from typing import Optional, cast
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
    PeriodComparisonParameters,
    PeriodComparisonResponse,
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
    base_currency: str = Depends(get_user_base_currency),
) -> SearchResponse[CategorySummaryResponse]:
    """
    Get categories with their transaction amounts for a specified period or date range.

    When no ``currency`` filter is set, multi-currency amounts are converted to the
    user's base currency before aggregation.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_categories_summary(
        user_id=user_id, parameters=parameters, base_currency=base_currency
    )


@router.get("/cashflow-summary", response_model=CashflowSummaryResponse)
def get_cashflow_summary(
    parameters: ReportingParameters = Depends(),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
    base_currency: str = Depends(get_user_base_currency),
) -> CashflowSummaryResponse:
    """
    Get income, expense, and total (net cashflow) for a period or date range.

    When no ``currency`` filter is set, multi-currency amounts are converted to the
    user's base currency before aggregation.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_cashflow_summary(
        user_id=user_id, parameters=parameters, base_currency=base_currency
    )


@router.get("/period-comparison", response_model=PeriodComparisonResponse)
def get_period_comparison(
    parameters: PeriodComparisonParameters = Depends(),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
    base_currency: str = Depends(get_user_base_currency),
) -> PeriodComparisonResponse:
    """
    Compare financial performance of current period vs previous equivalent period.

    When no ``currency`` filter is set, multi-currency amounts are converted to the
    user's base currency before aggregation.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_period_comparison(
        user_id=user_id, parameters=parameters, base_currency=base_currency
    )


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
