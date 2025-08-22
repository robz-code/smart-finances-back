import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.account import Account
from app.repository.account_repository import AccountRepository
from app.schemas.account_schemas import AccountUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class AccountService(BaseService[Account]):
    def __init__(self, db: Session) -> None:
        repository = AccountRepository(db)
        super().__init__(db, repository, Account)

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
                f"Attempt to update account with ID: {id} not owned by user with ID: {user_id}"
            )
            raise HTTPException(status_code=403, detail="You do not own this account")

        return True

    def before_delete(self, id: UUID, **kwargs: Any) -> Account:
        account = super().before_delete(id, **kwargs)

        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to delete account with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        if account.user_id != user_id:
            logger.warning(
                f"Attempt to delete account with ID: {id} not owned by user with ID: {user_id}"
            )
            raise HTTPException(status_code=403, detail="You do not own this account")

        return account
