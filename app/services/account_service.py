from app.services.base_service import BaseService
from app.repository.account_repository import AccountRepository


class AccountService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.repository = AccountRepository(db)
