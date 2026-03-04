"""Concept tools: list and retrieve transaction concepts."""

from uuid import UUID

from mcp_server.auth import get_user_id
from mcp_server.service_factory import build_concept_service, get_db
from mcp_server.utils import entity_to_dict, search_entities, to_json


def get_concepts(session_token: str) -> str:
    """
    Get all concepts (transaction labels/descriptions) for the authenticated user.

    Concepts are reusable descriptions that can be attached to transactions.
    Returns a list with id, name, and ownership info.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_concept_service(db)
        response = service.get_by_user_id(user_id)
        return search_entities(response)
    finally:
        db.close()


def get_concept(session_token: str, concept_id: str) -> str:
    """
    Get a single concept by its ID.

    The concept must belong to the authenticated user.
    Provide concept_id as a UUID string.
    """
    user_id = get_user_id(session_token)
    db = get_db()
    try:
        service = build_concept_service(db)
        concept = service.get(UUID(concept_id))
        if concept.user_id != user_id:
            raise ValueError("Concept not found or access denied.")
        return to_json(entity_to_dict(concept))
    finally:
        db.close()
