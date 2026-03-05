"""Category tools: list and retrieve categories."""

from typing import Optional
from uuid import UUID

from mcp_server.auth import get_user_id
from mcp_server.service_factory import build_category_service, get_db
from mcp_server.utils import entity_to_dict, to_json


def get_categories(session_token: str, type: Optional[str] = None) -> str:
    """
    Get all categories for the authenticated user.

    Args:
        session_token: Your session token from the login tool.
        type: Optional filter. Use 'income', 'expense', or 'transfer' to
              return only categories of that type. Leave empty for all categories.

    Returns a list with id, name, type, icon, color, and ownership info.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_category_service(db)
        if type:
            from app.entities.category import CategoryType
            response = service.get_by_user_id_and_type(user_id, CategoryType(type))
        else:
            response = service.get_by_user_id(user_id)
        results = [entity_to_dict(c) for c in response.results]
        return to_json({"total": response.total, "results": results})
    finally:
        db.close()


def get_category(session_token: str, category_id: str) -> str:
    """
    Get a single category by its ID.

    The category must belong to the authenticated user.
    Provide category_id as a UUID string.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_category_service(db)
        category = service.get(UUID(category_id))
        if category.user_id != user_id:
            raise ValueError("Category not found or access denied.")
        return to_json(entity_to_dict(category))
    finally:
        db.close()
