import logging
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.dependencies.auth_dependency import verify_token
from app.entities.user import User
from app.services.user_service import UserService

# Configure logger
logger = logging.getLogger(__name__)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_current_user(
    token_payload: dict = Depends(verify_token),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Dependency to get the current authenticated user from the token"""
    user_id_str = token_payload.get("sub")
    if not user_id_str:
        logger.error("Authentication failed: No user_id in token payload")
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_id = UUID(user_id_str)
    except Exception:
        logger.error("Authentication failed: Invalid user_id format in token payload")
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user = user_service.get(user_id)
        if not user:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        logger.debug(f"Successfully authenticated user: {user_id}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user authentication: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_user_base_currency(
    current_user: User = Depends(get_current_user),
) -> str:
    """Requires user to have a main currency set. Raises 422 if not."""
    if not current_user.currency or not current_user.currency.strip():
        raise HTTPException(
            status_code=422,
            detail="Main currency is required. Please set your currency in profile settings.",
        )
    return current_user.currency
