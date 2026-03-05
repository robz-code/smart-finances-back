"""
Thin adapter layer: wire existing app/dependencies/ functions for use
outside of FastAPI's DI context.

Since all dependency functions accept plain arguments (Depends() is only
a default-value marker), they can be called directly by passing `db`.
No logic is duplicated here — every factory delegates to the existing
dependency function.
"""

from sqlalchemy.orm import Session

from app.config.database import get_session_factory

# Re-export existing dependency functions under stable MCP-side names.
from app.dependencies.account_dependencies import get_account_repository
from app.dependencies.account_dependencies import get_account_service as build_account_service
from app.dependencies.balance_dependencies import get_balance_engine, get_fx_service
from app.dependencies.balance_snapshot_dependencies import get_balance_snapshot_repository
from app.dependencies.category_dependencies import get_category_service as build_category_service
from app.dependencies.concept_dependencies import get_concept_service as build_concept_service
from app.dependencies.reporting_dependencies import get_reporting_service
from app.dependencies.tag_dependencies import get_tag_service as build_tag_service
from app.dependencies.transaction_dependencies import (
    get_transaction_repository,
    get_transaction_service,
)
from app.dependencies.user_dependencies import get_user_service as build_user_service


def get_db() -> Session:
    """Open and return a new SQLAlchemy session. Caller is responsible for closing it."""
    return get_session_factory()()


def build_transaction_service(db: Session):
    """Compose TransactionService via the existing dependency function."""
    return get_transaction_service(
        db,
        build_account_service(db),
        build_category_service(db),
        build_concept_service(db),
        build_tag_service(db),
        get_balance_snapshot_repository(db),
    )


def build_reporting_service(db: Session):
    """Compose ReportingService via the existing dependency functions."""
    fx_svc = get_fx_service()
    balance_engine = get_balance_engine(
        account_repo=get_account_repository(db),
        snapshot_repo=get_balance_snapshot_repository(db),
        transaction_repo=get_transaction_repository(db),
        fx_service=fx_svc,
    )
    return get_reporting_service(
        category_service=build_category_service(db),
        transaction_service=build_transaction_service(db),
        balance_engine=balance_engine,
        fx_service=fx_svc,
    )
