"""Serialization helpers for MCP tool responses."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def _default(obj: Any) -> Any:
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "value"):  # Enum
        return obj.value
    if hasattr(obj, "model_dump"):  # Pydantic model
        return obj.model_dump(mode="json")
    raise TypeError(f"Type {type(obj).__name__} is not JSON serializable")


def to_json(obj: Any) -> str:
    """Serialize *obj* to a JSON string, handling common domain types."""
    return json.dumps(obj, default=_default)


def entity_to_dict(entity: Any) -> dict:
    """Convert a SQLAlchemy ORM entity to a plain dict (table columns only)."""
    return {col.name: getattr(entity, col.name, None) for col in entity.__table__.columns}


def search_entities(response: Any) -> str:
    """Serialize a SearchResponse whose results are SQLAlchemy entities."""
    results = [entity_to_dict(item) for item in response.results]
    return to_json({"total": response.total, "results": results})


def search_pydantic(response: Any) -> str:
    """Serialize a SearchResponse whose results are Pydantic models."""
    results = [item.model_dump(mode="json") for item in response.results]
    return to_json({"total": response.total, "results": results})
