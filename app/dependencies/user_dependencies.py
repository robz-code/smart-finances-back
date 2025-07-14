
from app.services.user_service import UserService
from app.config.database import get_db
from app.repository.user_repository import UserRepository
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies.auth_dependency import verify_token


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_current_user(
    token_payload: dict = Depends(verify_token),
    user_service: UserService = Depends(get_user_service)
):
    """Dependency to get the current authenticated user from the token"""
    user_id = token_payload.get("sub")
    if not user_id:
        print("No user_id in token payload")
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = user_service.get(user_id)
    if not user:
        print(f"User not found with ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
