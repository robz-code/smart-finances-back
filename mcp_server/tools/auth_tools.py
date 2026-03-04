"""Authentication tools: login and logout via Supabase."""

from app.config.settings import get_settings
from mcp_server.session import create_session, delete_session


def _get_supabase_client():
    from supabase import create_client

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError(
            "Supabase is not configured on this server. "
            "Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def login(email: str, password: str) -> str:
    """
    Authenticate with your Smart Finances account using email and password.

    Returns a session_token that must be passed to all other tools.
    Keep this token for the duration of your session.
    """
    try:
        client = _get_supabase_client()
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if not response.session or not response.session.access_token:
            raise ValueError("Login failed: Supabase returned no session.")

        jwt_token = response.session.access_token
        session_token = create_session(jwt_token)

        user_email = response.user.email if response.user else email
        return (
            f"Login successful. Authenticated as: {user_email}\n\n"
            f"session_token: {session_token}\n\n"
            f"Pass this session_token as the first argument to all other Smart Finances tools."
        )
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Login failed: {exc}")


def logout(session_token: str) -> str:
    """
    End the current session and invalidate the session_token.

    Call this when you are done to clean up the session.
    """
    delete_session(session_token)
    return "Successfully logged out. Your session has been invalidated."
