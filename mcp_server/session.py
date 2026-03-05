"""In-memory session store mapping session tokens to Supabase JWTs."""

import secrets
from typing import Dict, Optional

# { session_token: jwt_access_token }
_sessions: Dict[str, str] = {}


def create_session(jwt_token: str) -> str:
    """Store a JWT and return an opaque session token."""
    session_token = secrets.token_hex(32)
    _sessions[session_token] = jwt_token
    return session_token


def get_jwt(session_token: str) -> Optional[str]:
    """Return the JWT for a session token, or None if not found."""
    return _sessions.get(session_token)


def delete_session(session_token: str) -> None:
    """Remove a session."""
    _sessions.pop(session_token, None)
