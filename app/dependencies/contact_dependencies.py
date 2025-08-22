from app.services.contact_service import ContactService
from app.services.user_service import UserService
from app.dependencies.user_dependencies import get_user_service
from app.config.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from app.services.debt_service import DebtService
from app.dependencies.debt_dependencies import get_debt_service

def get_contact_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    debt_service: DebtService = Depends(get_debt_service)
) -> ContactService:
    return ContactService(db, user_service, debt_service)
