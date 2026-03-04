"""Factory functions that build domain services with a given DB session."""

from sqlalchemy.orm import Session

from app.config.database import get_session_factory
from app.engines.balance_engine import BalanceEngine
from app.repository.account_repository import AccountRepository
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.repository.transaction_repository import TransactionRepository
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.concept_service import ConceptService
from app.services.fx_service import FxService
from app.services.reporting_service import ReportingService
from app.services.tag_service import TagService
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService


def get_db() -> Session:
    """Open and return a new SQLAlchemy session. Caller is responsible for closing it."""
    return get_session_factory()()


def build_user_service(db: Session) -> UserService:
    return UserService(db)


def build_account_service(db: Session) -> AccountService:
    return AccountService(db)


def build_category_service(db: Session) -> CategoryService:
    return CategoryService(db)


def build_concept_service(db: Session) -> ConceptService:
    return ConceptService(db)


def build_tag_service(db: Session) -> TagService:
    return TagService(db)


def build_transaction_service(db: Session) -> TransactionService:
    return TransactionService(
        db,
        account_service=AccountService(db),
        category_service=CategoryService(db),
        concept_service=ConceptService(db),
        tag_service=TagService(db),
        balance_snapshot_repository=BalanceSnapshotRepository(db),
    )


def build_reporting_service(db: Session) -> ReportingService:
    fx_service = FxService()
    balance_engine = BalanceEngine(
        account_repo=AccountRepository(db),
        snapshot_repo=BalanceSnapshotRepository(db),
        transaction_repo=TransactionRepository(db),
        fx_service=fx_service,
    )
    return ReportingService(
        category_service=CategoryService(db),
        transaction_service=build_transaction_service(db),
        balance_engine=balance_engine,
        fx_service=fx_service,
    )
