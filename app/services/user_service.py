from typing import Optional, cast

from sqlalchemy.orm import Session

from app.entities.user import User
from app.repository.user_repository import UserRepository
from app.services.base_service import BaseService


class UserService(BaseService[User]):
    def __init__(self, db: Session) -> None:
        repository = UserRepository(db)
        super().__init__(db, repository, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        result = self.repository.get_by_email(email)
        return cast(Optional[User], result)
