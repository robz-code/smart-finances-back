from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.concept_service import ConceptService


def get_concept_service(db: Session = Depends(get_db)) -> ConceptService:
    return ConceptService(db)
