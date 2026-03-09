import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.account import Account
from app.repository.account_repository import AccountRepository
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository

# from app.schemas.account_schemas import AccountUpdate  # unused in service
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class AccountService(BaseService[Account]):
    def __init__(self, db: Session) -> None:
        repository = AccountRepository(db)
        super().__init__(db, repository, Account)
        self.balance_snapshot_repository = BalanceSnapshotRepository(db)

    def before_update(self, id: UUID, obj_in: Any, **kwargs: Any) -> bool:
        super().before_update(id, obj_in, **kwargs)

        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to update account with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Get the account to check ownership
        account = self.repository.get(id)
        if account and account.user_id != user_id:
            logger.warning(
                (
                    f"Attempt to update account with ID: {id} not owned by user "
                    f"with ID: {user_id}"
                )
            )
            raise HTTPException(status_code=403, detail="You do not own this account")

        return True

    def delete(self, id: UUID, **kwargs: Any) -> Optional[Account]:
        """Soft-delete an account: validate ownership, purge snapshots, set is_deleted=True."""
        account = self.before_delete(id, **kwargs)
        try:
            # Queue snapshot deletes (no commit yet)
            self.balance_snapshot_repository.delete_all_for_account(id)
            # Soft-delete the account — commits both changes atomically
            self.repository.soft_delete(id)  # type: ignore[attr-defined]
            logger.info(f"Soft-deleted account id={id}")
        except Exception:
            self.db.rollback()
            logger.exception(f"Failed to soft-delete account id={id}")
            raise
        return account

    def before_delete(self, id: UUID, **kwargs: Any) -> Account:
        account = super().before_delete(id, **kwargs)

        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to delete account with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        if account.user_id != user_id:
            logger.warning(
                (
                    f"Attempt to delete account with ID: {id} not owned by user "
                    f"with ID: {user_id}"
                )
            )
            raise HTTPException(status_code=403, detail="You do not own this account")

        return account
