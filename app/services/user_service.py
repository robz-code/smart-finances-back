from app.services.base_service import BaseService
from app.repository.user_repository import UserRepository
from app.entities.user import User

class UserService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.entity = User
        self.repository = UserRepository(db)

    def get_by_email(self, email: str):
        return self.repository.get_by_email(email)
