from app.services.contact_service import ContactService
from app.services.user_service import UserService
from app.config.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

def get_contact_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(lambda db: UserService(db))
) -> ContactService:
    return ContactService(db, user_service)