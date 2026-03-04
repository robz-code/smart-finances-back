"""Tag tools: list and retrieve transaction tags."""

from uuid import UUID

from mcp_server.auth import get_user_id
from mcp_server.service_factory import build_tag_service, get_db
from mcp_server.utils import entity_to_dict, search_entities, to_json


def get_tags(session_token: str) -> str:
    """
    Get all tags for the authenticated user.

    Tags can be attached to transactions for flexible categorization.
    Returns a list with id, name, and ownership info.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_tag_service(db)
        response = service.get_by_user_id(user_id)
        return search_entities(response)
    finally:
        db.close()


def get_tag(session_token: str, tag_id: str) -> str:
    """
    Get a single tag by its ID.

    The tag must belong to the authenticated user.
    Provide tag_id as a UUID string.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_tag_service(db)
        tag = service.get(UUID(tag_id))
        if tag.user_id != user_id:
            raise ValueError("Tag not found or access denied.")
        return to_json(entity_to_dict(tag))
    finally:
        db.close()
