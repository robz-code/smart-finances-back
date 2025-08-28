from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.transaction_service import TransactionService


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    return TransactionService(db)