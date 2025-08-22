from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.tag_service import TagService


def get_tag_service(db: Session = Depends(get_db)) -> TagService:
    return TagService(db)
