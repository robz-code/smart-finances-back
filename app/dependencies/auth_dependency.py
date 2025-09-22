import os
from typing import Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.settings import get_settings

bearer_scheme = HTTPBearer(
    description="Enter your JWT token in the format: Bearer <token>",
    auto_error=False,
)


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        settings = get_settings()
        # Prefer runtime environment secret in tests; fallback to settings
        secret = os.getenv("JWT_SECRET_KEY", settings.JWT_SECRET_KEY)
        payload = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        print("Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")
