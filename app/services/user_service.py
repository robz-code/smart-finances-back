from app.services.base_service import BaseService
from app.repository.user_repository import UserRepository
from app.entities.user import User
from typing import Optional

class UserService(BaseService[User]):
    def __init__(self, db):
        repository = UserRepository(db)
        super().__init__(db, repository, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.repository.get_by_email(email)
