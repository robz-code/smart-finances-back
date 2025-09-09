from typing import Any, Optional, cast

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

    def add(self, obj_in: User, **kwargs: Any) -> User:  # type: ignore[override]
        """Add new user or return existing user with the same email."""
        existing = self.get_by_email(obj_in.email)
        if existing:
            # Update existing user's ID to match the provided one so that
            # subsequent operations using the token's subject succeed.
            existing.id = obj_in.id
            self.db.commit()
            self.db.refresh(existing)
            return existing
        return super().add(obj_in, **kwargs)
