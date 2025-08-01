from app.repository.base_repository import BaseRepository
from sqlalchemy.orm import Session
from app.entities.account import Account


class AccountRepository(BaseRepository[Account]):
    def __init__(self, db: Session):
        super().__init__(db, Account)
