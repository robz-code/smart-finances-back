from app.services.base_service import BaseService
from app.repository.user_repository import UserRepository



class UserService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.repository = UserRepository(db)

    def get_by_email(self, email: str):
        return self.repository.get_by_email(email)