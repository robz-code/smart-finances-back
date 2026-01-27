from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.budget_service import BudgetService


def get_budget_service(db: Session = Depends(get_db)) -> BudgetService:
    return BudgetService(db)
