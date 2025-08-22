from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.account_service import AccountService


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)
