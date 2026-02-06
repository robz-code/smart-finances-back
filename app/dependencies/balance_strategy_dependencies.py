"""Dependencies for balance strategy factory."""

from fastapi import Depends

from app.dependencies.account_dependencies import get_account_repository
from app.dependencies.balance_dependencies import get_fx_service
from app.dependencies.balance_snapshot_dependencies import (
    get_balance_snapshot_repository,
)
from app.dependencies.transaction_dependencies import get_transaction_repository
from app.engines.balance.factory import BalanceStrategyFactory
from app.repository.account_repository import AccountRepository
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.repository.transaction_repository import TransactionRepository
from app.services.fx_service import FxService


def get_balance_strategy_factory(
    account_repo: AccountRepository = Depends(get_account_repository),
    snapshot_repo: BalanceSnapshotRepository = Depends(
        get_balance_snapshot_repository
    ),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    fx_service: FxService = Depends(get_fx_service),
) -> BalanceStrategyFactory:
    """Factory for creating balance strategies with injected dependencies."""
    return BalanceStrategyFactory(
        account_repo=account_repo,
        snapshot_repo=snapshot_repo,
        transaction_repo=transaction_repo,
        fx_service=fx_service,
    )
