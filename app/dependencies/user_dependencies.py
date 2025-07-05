
from app.services.user_service import UserService
from app.config.database import get_db
from app.repository.user_repository import UserRepository
from fastapi import Depends
from sqlalchemy.orm import Session


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)
