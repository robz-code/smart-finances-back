"""Dependencies for balance service, snapshot service, and balance engine."""

from fastapi import Depends

from app.config.settings import get_settings
from app.dependencies.account_dependencies import (
    get_account_repository,
    get_account_service,
)
from app.dependencies.balance_snapshot_dependencies import (
    get_balance_snapshot_repository,
)
from app.dependencies.transaction_dependencies import (
    get_transaction_repository,
    get_transaction_service,
)
from app.engines.balance_engine import BalanceEngine
from app.repository.account_repository import AccountRepository
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.repository.transaction_repository import TransactionRepository
from app.services.account_service import AccountService
from app.services.fx_client import FxClient
from app.services.fx_service import FxService
from app.services.snapshot_service import SnapshotService
from app.services.transaction_service import TransactionService


def get_fx_service() -> FxService:
    """FX service backed by FastForex API (falls back to 1:1 if no key configured)."""
    settings = get_settings()
    client = None
    if settings.FX_API_KEY:
        client = FxClient(
            api_key=settings.FX_API_KEY,
            base_url=settings.FX_API_BASE_URL,
        )
    return FxService(fx_client=client)


def get_balance_engine(
    account_repo: AccountRepository = Depends(get_account_repository),
    snapshot_repo: BalanceSnapshotRepository = Depends(get_balance_snapshot_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    fx_service: FxService = Depends(get_fx_service),
) -> BalanceEngine:
    """Balance engine for balance reporting computations (repos + FX injected)."""
    return BalanceEngine(
        account_repo=account_repo,
        snapshot_repo=snapshot_repo,
        transaction_repo=transaction_repo,
        fx_service=fx_service,
    )


def get_snapshot_service(
    account_service: AccountService = Depends(get_account_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
    balance_snapshot_repository: BalanceSnapshotRepository = Depends(
        get_balance_snapshot_repository
    ),
) -> SnapshotService:
    """Snapshot service with injected dependencies."""
    return SnapshotService(
        account_service=account_service,
        transaction_service=transaction_service,
        balance_snapshot_repository=balance_snapshot_repository,
    )
