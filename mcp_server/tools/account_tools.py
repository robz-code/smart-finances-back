"""Account tools: list and retrieve accounts."""

from uuid import UUID

from mcp_server.auth import get_user_id
from mcp_server.service_factory import build_account_service, get_db
from mcp_server.utils import entity_to_dict, search_entities, to_json


def get_accounts(session_token: str) -> str:
    """
    Get all accounts belonging to the authenticated user.

    Returns a list of accounts with their id, name, type, currency,
    color, initial_balance, and creation dates.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_account_service(db)
        response = service.get_by_user_id(user_id)
        return search_entities(response)
    finally:
        db.close()


def get_account(session_token: str, account_id: str) -> str:
    """
    Get a single account by its ID.

    The account must belong to the authenticated user.
    Provide account_id as a UUID string.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_account_service(db)
        account = service.get(UUID(account_id))
        if account.user_id != user_id:
            raise ValueError("Account not found or access denied.")
        return to_json(entity_to_dict(account))
    finally:
        db.close()
