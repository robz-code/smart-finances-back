import logging
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.account import Account
from app.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AccountRepository(BaseRepository[Account]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Account)

    def get(self, id: UUID) -> Account:
        """Get an active (non-deleted) account by ID. Raises 404 if not found or soft-deleted."""
        logger.debug(f"DB get: Account id={id} (is_deleted=False filter)")
        account = (
            self.db.query(Account)
            .filter(Account.id == id, Account.is_deleted == False)  # noqa: E712
            .first()
        )
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        return account

    def get_by_user_id(self, user_id: UUID) -> List[Account]:
        """Get all active (non-deleted) accounts for a user."""
        logger.debug(
            f"DB get_by_user_id: Account user_id={user_id} (is_deleted=False filter)"
        )
        return (
            self.db.query(Account)
            .filter(
                Account.user_id == user_id, Account.is_deleted == False
            )  # noqa: E712
            .all()
        )

    def soft_delete(self, id: UUID) -> None:
        """Mark an account as deleted (is_deleted=True) and commit."""
        logger.debug(f"DB soft_delete: Account id={id}")
        self.db.query(Account).filter(Account.id == id).update(
            {"is_deleted": True}, synchronize_session=False
        )
        self.db.commit()
        logger.info(f"Soft-deleted Account with ID: {id}")
