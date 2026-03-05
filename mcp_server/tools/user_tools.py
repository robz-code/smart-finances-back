"""User tools: read the authenticated user's profile."""

from mcp_server.auth import get_user_id
from mcp_server.service_factory import build_user_service, get_db
from mcp_server.utils import entity_to_dict, to_json


def get_user_profile(session_token: str) -> str:
    """
    Get the profile of the currently authenticated user.

    Returns name, email, currency, language, and other profile fields.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_user_service(db)
        user = service.get(user_id)
        return to_json(entity_to_dict(user))
    finally:
        db.close()
