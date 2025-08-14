from fastapi import Depends
from app.services.category_service import CategoryService
from app.config.database import get_db
from sqlalchemy.orm import Session


def get_category_service(db: Session = Depends(get_db)):
    return CategoryService(db)

