"""Transaction tools: search, recent, and retrieve individual transactions."""

from typing import Optional
from uuid import UUID

from mcp_server.auth import get_user_id
from mcp_server.service_factory import build_transaction_service, get_db
from mcp_server.utils import search_pydantic, to_json


def search_transactions(
    session_token: str,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    type: Optional[str] = None,
    currency: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    period: Optional[str] = None,
    amount_min: Optional[str] = None,
    amount_max: Optional[str] = None,
    source: Optional[str] = None,
) -> str:
    """
    Search transactions with optional filters.

    All parameters are optional. Combine them to narrow results.

    Args:
        session_token: Your session token from the login tool.
        account_id: Filter by account UUID.
        category_id: Filter by category UUID.
        type: 'income' or 'expense'.
        currency: Currency code, e.g. 'MXN', 'USD'.
        date_from: Start date in YYYY-MM-DD format (use with date_to).
        date_to: End date in YYYY-MM-DD format (use with date_from).
        period: Predefined period: 'day', 'week', 'month', or 'year'.
                Use EITHER period OR date_from/date_to, not both.
        amount_min: Minimum transaction amount (decimal string, e.g. '100.00').
        amount_max: Maximum transaction amount (decimal string, e.g. '5000.00').
        source: Transaction source, e.g. 'manual'.

    Returns paginated results with total count and transaction list.
    """
    from datetime import date
    from decimal import Decimal

    from app.schemas.transaction_schemas import TransactionSearch

    user_id = get_user_id(session_token)

    search_params = TransactionSearch(
        account_id=UUID(account_id) if account_id else None,
        category_id=UUID(category_id) if category_id else None,
        type=type,
        currency=currency,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        period=period,
        amount_min=Decimal(amount_min) if amount_min else None,
        amount_max=Decimal(amount_max) if amount_max else None,
        source=source,
    )

    db = get_db()
    try:
        service = build_transaction_service(db)
        response = service.search(user_id, search_params)
        return search_pydantic(response)
    finally:
        db.close()


def get_recent_transactions(session_token: str, limit: int = 10) -> str:
    """
    Get the most recent transactions for the authenticated user.

    Args:
        session_token: Your session token from the login tool.
        limit: Number of transactions to return. Must be one of: 5, 10, 20, 50, 100.
               Defaults to 10.

    Returns the most recent transactions ordered by date descending.
    """
    from app.schemas.transaction_schemas import RecentTransactionsParams

    user_id = get_user_id(session_token)

    params = RecentTransactionsParams(limit=limit)

    db = get_db()
    try:
        service = build_transaction_service(db)
        response = service.get_recent(user_id, params)
        results = [tx.model_dump(mode="json") for tx in response.results]
        return to_json({"total": len(results), "results": results})
    finally:
        db.close()


def get_transaction(session_token: str, transaction_id: str) -> str:
    """
    Get a single transaction by its ID.

    The transaction must belong to the authenticated user.
    Provide transaction_id as a UUID string.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_transaction_service(db)
        tx = service.get(UUID(transaction_id), user_id)
        return to_json(tx.model_dump(mode="json"))
    finally:
        db.close()
