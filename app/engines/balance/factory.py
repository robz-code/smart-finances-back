"""
Factory for balance strategies. Injects repositories and services.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from app.engines.balance.strategies import (
    BalanceHistoryStrategy,
    PerAccountBalanceAtDateStrategy,
    TotalBalanceAtDateStrategy,
)
from app.repository.account_repository import AccountRepository
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.repository.transaction_repository import TransactionRepository
from app.services.fx_service import FxService


class BalanceStrategyFactory:
    """Creates balance strategies with injected dependencies."""

    def __init__(
        self,
        account_repo: AccountRepository,
        snapshot_repo: BalanceSnapshotRepository,
        transaction_repo: TransactionRepository,
        fx_service: FxService,
    ):
        self.account_repo = account_repo
        self.snapshot_repo = snapshot_repo
        self.transaction_repo = transaction_repo
        self.fx_service = fx_service

    def create_total_balance_strategy(
        self, user_id: UUID, as_of: date, base_currency: str
    ) -> TotalBalanceAtDateStrategy:
        return TotalBalanceAtDateStrategy(
            user_id=user_id,
            as_of=as_of,
            base_currency=base_currency,
            account_repo=self.account_repo,
            snapshot_repo=self.snapshot_repo,
            transaction_repo=self.transaction_repo,
            fx_service=self.fx_service,
        )

    def create_per_account_balance_strategy(
        self, user_id: UUID, as_of: date, base_currency: str
    ) -> PerAccountBalanceAtDateStrategy:
        return PerAccountBalanceAtDateStrategy(
            user_id=user_id,
            as_of=as_of,
            base_currency=base_currency,
            account_repo=self.account_repo,
            snapshot_repo=self.snapshot_repo,
            transaction_repo=self.transaction_repo,
            fx_service=self.fx_service,
        )

    def create_balance_history_strategy(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        period: str,
        base_currency: str,
        account_id: Optional[UUID] = None,
    ) -> BalanceHistoryStrategy:
        return BalanceHistoryStrategy(
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            period=period,
            base_currency=base_currency,
            account_id=account_id,
            account_repo=self.account_repo,
            snapshot_repo=self.snapshot_repo,
            transaction_repo=self.transaction_repo,
            fx_service=self.fx_service,
        )
