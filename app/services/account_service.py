from app.services.base_service import BaseService
from app.repository.account_repository import AccountRepository
from app.entities.account import Account

class AccountService(BaseService[Account]):
    def __init__(self, db):
        repository = AccountRepository(db)
        super().__init__(db, repository, Account)
