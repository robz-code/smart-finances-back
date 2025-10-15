from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.installment_service import InstallmentService


def get_installment_service(db: Session = Depends(get_db)) -> InstallmentService:
    return InstallmentService(db)
