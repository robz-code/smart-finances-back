from sqlalchemy.orm import Session

from app.entities.account import Account
from app.repository.base_repository import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Account)
