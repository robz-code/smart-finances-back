from app.services.contact_service import ContactService
from app.services.user_service import UserService
from app.config.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from app.dependencies.user_dependencies import get_user_service

def get_contact_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
) -> ContactService:
    return ContactService(db, user_service)