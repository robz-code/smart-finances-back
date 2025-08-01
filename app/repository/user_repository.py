from app.repository.base_repository import BaseRepository
from sqlalchemy.orm import Session
from app.entities.user import User
from typing import Optional


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.db.query(User).filter(User.email == email).first()
    