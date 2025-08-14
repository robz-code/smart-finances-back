from dotenv.main import logger
from app.services.base_service import BaseService
from app.repository.account_repository import AccountRepository
from app.entities.account import Account
from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from app.schemas.account_schemas import AccountUpdate
import logging

logger = logging.getLogger(__name__)
class AccountService(BaseService[Account]):
    def __init__(self, db):
        repository = AccountRepository(db)
        super().__init__(db, repository, Account)


    def before_update(self, id: UUID, obj_in: AccountUpdate, **kwargs) -> Account:
        account =  super().before_update(id, obj_in, **kwargs)

        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to update account with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        if account.user_id != user_id:
            logger.warning(f"Attempt to update account with ID: {id} not owned by user with ID: {user_id}")
            raise HTTPException(status_code=403, detail=f"You do not own this account")
        
        return account


    def before_delete(self, id: UUID, **kwargs) -> Account:
        account = super().before_delete(id, **kwargs)
        
        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to delete account with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        if account.user_id != user_id: 
            logger.warning(f"Attempt to delete account with ID: {id} not owned by user with ID: {user_id}")
            raise HTTPException(status_code=403, detail=f"You do not own this account")
        
        return account

