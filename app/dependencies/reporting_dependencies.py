from fastapi import Depends

from app.dependencies.balance_dependencies import get_balance_engine, get_fx_service
from app.dependencies.category_dependencies import get_category_service
from app.dependencies.transaction_dependencies import get_transaction_service
from app.engines.balance_engine import BalanceEngine
from app.services.category_service import CategoryService
from app.services.fx_service import FxService
from app.services.reporting_service import ReportingService
from app.services.transaction_service import TransactionService


def get_reporting_service(
    category_service: CategoryService = Depends(get_category_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
    balance_engine: BalanceEngine = Depends(get_balance_engine),
    fx_service: FxService = Depends(get_fx_service),
) -> ReportingService:
    """Dependency factory for ReportingService with injected domain services."""
    return ReportingService(
        category_service,
        transaction_service,
        balance_engine,
        fx_service,
    )
