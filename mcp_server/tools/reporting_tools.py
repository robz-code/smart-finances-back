"""Reporting tools: cashflow, categories summary, balance, and comparisons."""

from typing import Optional
from uuid import UUID

from mcp_server.auth import get_user_id
from mcp_server.service_factory import build_reporting_service, build_user_service, get_db
from mcp_server.utils import to_json


def _resolve_currency(db, user_id: UUID, currency: Optional[str]) -> str:
    """Return *currency* if provided, otherwise use the user's base currency."""
    if currency:
        return currency
    user = build_user_service(db).get(user_id)
    if not user.currency:
        raise ValueError(
            "No currency provided and your profile has no base currency set. "
            "Please pass a currency code (e.g. 'MXN') or update your profile."
        )
    return user.currency


def get_categories_summary(
    session_token: str,
    period: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    type: Optional[str] = None,
    category_id: Optional[str] = None,
    account_id: Optional[str] = None,
    currency: Optional[str] = None,
    amount_min: Optional[str] = None,
    amount_max: Optional[str] = None,
    source: Optional[str] = None,
    full_list: bool = True,
) -> str:
    """
    Get categories with their net transaction amounts for a time period.

    Provide EITHER period OR date_from + date_to (period takes precedence).

    Args:
        session_token: Your session token from the login tool.
        period: Predefined period: 'day', 'week', 'month', or 'year'.
        date_from: Start date YYYY-MM-DD (use with date_to when period is not set).
        date_to: End date YYYY-MM-DD (use with date_from when period is not set).
        type: Filter by category type: 'income' or 'expense'.
        category_id: Restrict to a single category UUID.
        account_id: Filter transactions by account UUID.
        currency: Filter transactions by currency code.
        amount_min: Minimum transaction amount.
        amount_max: Maximum transaction amount.
        source: Filter by transaction source.
        full_list: If True (default), include categories with 0 transactions.
                   If False, return only categories that have matching transactions.

    Returns categories with transaction_amount (net-signed) and transaction_count.
    """
    from datetime import date
    from decimal import Decimal

    from app.schemas.reporting_schemas import ReportingParameters

    user_id = get_user_id(session_token)
    params = ReportingParameters(
        period=period,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        type=type,
        category_id=UUID(category_id) if category_id else None,
        account_id=UUID(account_id) if account_id else None,
        currency=currency,
        amount_min=Decimal(amount_min) if amount_min else None,
        amount_max=Decimal(amount_max) if amount_max else None,
        source=source,
        full_list=full_list,
    )
    db = get_db()
    try:
        service = build_reporting_service(db)
        response = service.get_categories_summary(user_id=user_id, parameters=params)
        results = [item.model_dump(mode="json") for item in response.results]
        return to_json({"total": response.total, "results": results})
    finally:
        db.close()


def get_cashflow_summary(
    session_token: str,
    period: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    type: Optional[str] = None,
    category_id: Optional[str] = None,
    account_id: Optional[str] = None,
    currency: Optional[str] = None,
    amount_min: Optional[str] = None,
    amount_max: Optional[str] = None,
    source: Optional[str] = None,
) -> str:
    """
    Get income, expense, and net cashflow totals for a period.

    Provide EITHER period OR date_from + date_to.

    Args:
        session_token: Your session token from the login tool.
        period: 'day', 'week', 'month', or 'year'.
        date_from: Start date YYYY-MM-DD.
        date_to: End date YYYY-MM-DD.
        type: Category type filter: 'income' or 'expense'.
        category_id: Filter to a single category UUID.
        account_id: Filter by account UUID.
        currency: Filter by currency code.
        amount_min: Minimum amount filter.
        amount_max: Maximum amount filter.
        source: Transaction source filter.

    Returns {{ income, expense, total }} all as decimal strings.
    """
    from datetime import date
    from decimal import Decimal

    from app.schemas.reporting_schemas import ReportingParameters

    user_id = get_user_id(session_token)
    params = ReportingParameters(
        period=period,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        type=type,
        category_id=UUID(category_id) if category_id else None,
        account_id=UUID(account_id) if account_id else None,
        currency=currency,
        amount_min=Decimal(amount_min) if amount_min else None,
        amount_max=Decimal(amount_max) if amount_max else None,
        source=source,
    )
    db = get_db()
    try:
        service = build_reporting_service(db)
        response = service.get_cashflow_summary(user_id=user_id, parameters=params)
        return to_json(response.model_dump(mode="json"))
    finally:
        db.close()


def get_period_comparison(
    session_token: str,
    period: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    currency: Optional[str] = None,
    amount_min: Optional[str] = None,
    amount_max: Optional[str] = None,
    source: Optional[str] = None,
) -> str:
    """
    Compare current period cashflow vs the previous equivalent period.

    Useful for detecting trends: 'this month vs last month'.

    Provide EITHER period OR date_from + date_to.

    Args:
        session_token: Your session token from the login tool.
        period: 'week', 'month', or 'year'.
        date_from: Custom period start YYYY-MM-DD.
        date_to: Custom period end YYYY-MM-DD.
        account_id: Filter by account UUID.
        category_id: Filter to one category UUID.
        currency: Filter by currency.
        amount_min: Minimum amount.
        amount_max: Maximum amount.
        source: Transaction source filter.

    Returns current_period, previous_period metrics, and a summary with
    difference, percentage_change, and trend ('up'|'down'|'flat').
    """
    from datetime import date
    from decimal import Decimal

    from app.schemas.reporting_schemas import PeriodComparisonParameters

    user_id = get_user_id(session_token)
    params = PeriodComparisonParameters(
        period=period,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        account_id=UUID(account_id) if account_id else None,
        category_id=UUID(category_id) if category_id else None,
        currency=currency,
        amount_min=Decimal(amount_min) if amount_min else None,
        amount_max=Decimal(amount_max) if amount_max else None,
        source=source,
    )
    db = get_db()
    try:
        service = build_reporting_service(db)
        response = service.get_period_comparison(user_id=user_id, parameters=params)
        return to_json(response.model_dump(mode="json"))
    finally:
        db.close()


def get_cashflow_history(
    session_token: str,
    date_from: str,
    date_to: str,
    period: str = "month",
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    currency: Optional[str] = None,
    amount_min: Optional[str] = None,
    amount_max: Optional[str] = None,
    source: Optional[str] = None,
) -> str:
    """
    Get historical cashflow series grouped by time period.

    Ideal for charts showing income and expense trends over time.

    Args:
        session_token: Your session token from the login tool.
        date_from: Series start date YYYY-MM-DD (required).
        date_to: Series end date YYYY-MM-DD (required).
        period: Grouping granularity: 'day', 'week', or 'month'. Defaults to 'month'.
        account_id: Filter by account UUID.
        category_id: Filter to one category UUID.
        currency: If provided, filter to this currency only.
                  If omitted, amounts are FX-converted to the user's base currency.
        amount_min: Minimum amount filter.
        amount_max: Maximum amount filter.
        source: Transaction source filter.

    Returns a list of points with period_start, income, expense, and net.
    """
    from datetime import date
    from decimal import Decimal

    from app.schemas.reporting_schemas import CashflowHistoryParameters

    user_id = get_user_id(session_token)
    params = CashflowHistoryParameters(
        date_from=date.fromisoformat(date_from),
        date_to=date.fromisoformat(date_to),
        period=period,
        account_id=UUID(account_id) if account_id else None,
        category_id=UUID(category_id) if category_id else None,
        currency=currency,
        amount_min=Decimal(amount_min) if amount_min else None,
        amount_max=Decimal(amount_max) if amount_max else None,
        source=source,
    )
    db = get_db()
    try:
        base_currency = _resolve_currency(db, user_id, currency)
        service = build_reporting_service(db)
        response = service.get_cashflow_history_response(
            user_id=user_id,
            parameters=params,
            base_currency=base_currency,
        )
        return to_json(response.model_dump(mode="json"))
    finally:
        db.close()


def get_balance(
    session_token: str,
    as_of: Optional[str] = None,
    currency: Optional[str] = None,
) -> str:
    """
    Get the user's total balance as of a date (defaults to today).

    Balance is computed from transactions and converted to the user's base
    currency (or the currency you specify).

    Args:
        session_token: Your session token from the login tool.
        as_of: Date YYYY-MM-DD to compute balance as of. Defaults to today.
        currency: Currency to express the balance in.
                  Defaults to the user's profile base currency.

    Returns {{ as_of, currency, balance }}.
    """
    from datetime import date

    user_id = get_user_id(session_token)
    db = get_db()
    try:
        base_currency = _resolve_currency(db, user_id, currency)
        service = build_reporting_service(db)
        as_of_date = date.fromisoformat(as_of) if as_of else None
        response = service.get_balance_response(
            user_id, currency=base_currency, as_of=as_of_date
        )
        return to_json(response.model_dump(mode="json"))
    finally:
        db.close()


def get_balance_accounts(
    session_token: str,
    as_of: Optional[str] = None,
    currency: Optional[str] = None,
) -> str:
    """
    Get the balance per account as of a date (defaults to today).

    Each account shows its native balance and the balance converted to
    the base currency.

    Args:
        session_token: Your session token from the login tool.
        as_of: Date YYYY-MM-DD. Defaults to today.
        currency: Base currency for conversion. Defaults to user's profile currency.

    Returns {{ as_of, currency, total, accounts: [...] }}.
    """
    from datetime import date

    user_id = get_user_id(session_token)
    db = get_db()
    try:
        base_currency = _resolve_currency(db, user_id, currency)
        service = build_reporting_service(db)
        as_of_date = date.fromisoformat(as_of) if as_of else None
        response = service.get_balance_accounts_response(
            user_id, currency=base_currency, as_of=as_of_date
        )
        return to_json(response.model_dump(mode="json"))
    finally:
        db.close()


def get_balance_history(
    session_token: str,
    date_from: str,
    date_to: str,
    period: str = "month",
    account_id: Optional[str] = None,
    currency: Optional[str] = None,
) -> str:
    """
    Get balance history for charts or lists.

    Shows how the total (or per-account) balance evolved over time.

    Args:
        session_token: Your session token from the login tool.
        date_from: Series start date YYYY-MM-DD (required).
        date_to: Series end date YYYY-MM-DD (required).
        period: Granularity: 'day', 'week', or 'month'. Defaults to 'month'.
                Note: 'year' is not supported for balance history.
        account_id: Optional UUID to filter to a single account.
        currency: Base currency for conversion. Defaults to user's profile currency.

    Returns {{ currency, period, points: [{{ date, balance }}, ...] }}.
    """
    from datetime import date

    from app.schemas.reporting_schemas import TransactionSummaryPeriod

    user_id = get_user_id(session_token)
    db = get_db()
    try:
        base_currency = _resolve_currency(db, user_id, currency)
        service = build_reporting_service(db)
        response = service.get_balance_history_response(
            user_id,
            from_date=date.fromisoformat(date_from),
            to_date=date.fromisoformat(date_to),
            currency=base_currency,
            period=TransactionSummaryPeriod(period),
            account_id=UUID(account_id) if account_id else None,
        )
        return to_json(response.model_dump(mode="json"))
    finally:
        db.close()
