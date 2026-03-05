"""Auth helper: resolve user_id from a session token."""

import os
from uuid import UUID

import jwt

from app.config.settings import get_settings
from mcp_server.session import get_jwt


def get_user_id(session_token: str) -> UUID:
    """
    Decode the JWT stored for *session_token* and return the user UUID.

    Raises ValueError with a human-friendly message on any auth failure so
    the MCP agent can relay it back to the user.
    """
    raw_jwt = get_jwt(session_token)
    if not raw_jwt:
        raise ValueError(
            "Not authenticated. Please call the 'login' tool first "
            "and use the returned session_token."
        )

    settings = get_settings()
    secret = os.getenv("JWT_SECRET_KEY", settings.JWT_SECRET_KEY)

    try:
        payload = jwt.decode(
            raw_jwt,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Session expired. Please call 'login' again.")
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid session: {exc}. Please call 'login' again.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise ValueError("Token has no user ID. Please call 'login' again.")

    try:
        return UUID(user_id_str)
    except ValueError:
        raise ValueError("Token contains an invalid user ID. Please call 'login' again.")
