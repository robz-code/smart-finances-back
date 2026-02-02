from fastapi import Depends

from app.dependencies.account_dependencies import get_account_service
from app.dependencies.balance_snapshot_dependencies import get_balance_snapshot_repository
from app.dependencies.category_dependencies import get_category_service
from app.dependencies.transaction_dependencies import get_transaction_service
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.fx_service import FxService
from app.services.reporting_service import ReportingService
from app.services.transaction_service import TransactionService


def get_fx_service() -> FxService:
    """Stub FX service; replace with real implementation when needed."""
    return FxService()


def get_reporting_service(
    category_service: CategoryService = Depends(get_category_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
    account_service: AccountService = Depends(get_account_service),
    balance_snapshot_repository: BalanceSnapshotRepository = Depends(
        get_balance_snapshot_repository
    ),
    fx_service: FxService = Depends(get_fx_service),
) -> ReportingService:
    """Dependency factory for ReportingService with injected domain services."""
    return ReportingService(
        category_service,
        transaction_service,
        account_service,
        balance_snapshot_repository,
        fx_service,
    )
