from fastapi import Depends
from sqlalchemy.orm import Session
from app.services.account_service import AccountService
from app.config.database import get_db


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)