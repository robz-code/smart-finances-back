from app.services.debt_service import DebtService
from app.config.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

def get_debt_service(db: Session = Depends(get_db)) -> DebtService:
    return DebtService(db)