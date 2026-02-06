from fastapi import Depends

from app.dependencies.account_dependencies import get_account_service
from app.dependencies.balance_strategy_dependencies import (
    get_balance_strategy_factory,
)
from app.dependencies.category_dependencies import get_category_service
from app.dependencies.transaction_dependencies import get_transaction_service
from app.engines.balance.factory import BalanceStrategyFactory
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.reporting_service import ReportingService
from app.services.transaction_service import TransactionService


def get_reporting_service(
    category_service: CategoryService = Depends(get_category_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
    account_service: AccountService = Depends(get_account_service),
    balance_strategy_factory: BalanceStrategyFactory = Depends(
        get_balance_strategy_factory
    ),
) -> ReportingService:
    """Dependency factory for ReportingService with injected domain services."""
    return ReportingService(
        category_service,
        transaction_service,
        account_service,
        balance_strategy_factory,
    )
