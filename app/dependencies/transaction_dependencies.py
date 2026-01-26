from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.dependencies.account_dependencies import get_account_service
from app.dependencies.category_dependencies import get_category_service
from app.dependencies.concept_dependencies import get_concept_service
from app.dependencies.tag_dependencies import get_tag_service
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.concept_service import ConceptService
from app.services.tag_service import TagService
from app.services.transaction_service import TransactionService


def get_transaction_service(
    db: Session = Depends(get_db),
    account_service: AccountService = Depends(get_account_service),
    category_service: CategoryService = Depends(get_category_service),
    concept_service: ConceptService = Depends(get_concept_service),
    tag_service: TagService = Depends(get_tag_service),
) -> TransactionService:
    """Dependency factory for TransactionService with injected domain services"""
    return TransactionService(
        db, account_service, category_service, concept_service, tag_service
    )
