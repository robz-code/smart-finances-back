"""
Balance service: per-account balance, totals, and history.

Uses snapshots for performance. Delegates complex history iteration to
BalanceEngine. Acts as factory/facade for balance operations.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.entities.balance_snapshot import BalanceSnapshot
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.services.account_service import AccountService
from app.services.fx_service import FxService
from app.services.transaction_service import TransactionService
from app.engines.balance_engine import BalanceEngine
from app.shared.helpers.date_helper import first_day_of_month

logger = logging.getLogger(__name__)


class BalanceService:
    """
    Balance domain service. Per-account balance, totals, history.

    Uses BalanceSnapshotRepository for snapshots, TransactionService for
    net sums, FxService for conversion. Delegates history iteration to
    BalanceEngine.
    """

    def __init__(
        self,
        account_service: AccountService,
        transaction_service: TransactionService,
        balance_snapshot_repository: BalanceSnapshotRepository,
        fx_service: FxService,
        balance_engine: BalanceEngine,
    ):
        self.account_service = account_service
        self.transaction_service = transaction_service
        self.balance_snapshot_repository = balance_snapshot_repository
        self.fx_service = fx_service
        self.balance_engine = balance_engine

    def get_account_balance(
        self, account_id: UUID, as_of: date
    ) -> tuple[Decimal, str]:
        """
        Compute native balance for one account as of a date.

        Uses snapshots + transactions. If no snapshot exists for the month,
        computes balance at start of month and stores it lazily (snapshots are
        rebuildable). Snapshot represents balance at start of snapshot_date;
        transactions included when snapshot_date < transaction_date <= as_of.
        """
        account = self.account_service.get(account_id)
        currency = account.currency
        initial = Decimal(str(account.initial_balance or 0))

        month_start = first_day_of_month(as_of)
        snap = self.balance_snapshot_repository.get_latest_before_or_on(
            account_id, as_of
        )

        logger.debug(
            f"Starting snapshot lookup for account {account_id} as of {as_of}"
        )

        if snap:
            base = Decimal(str(snap.balance))
            snap_date = snap.snapshot_date
            day_after_snap = snap_date + timedelta(days=1)
            delta = self.transaction_service.get_net_signed_sum_for_account(
                account_id, day_after_snap, as_of
            )
            return (base + delta, currency)
        else:
            day_before_month = month_start - timedelta(days=1)
            snap_before = self.balance_snapshot_repository.get_latest_before(
                account_id, month_start
            )
            if snap_before:
                base = Decimal(str(snap_before.balance))
                day_after_snap = snap_before.snapshot_date + timedelta(days=1)
                sum_before = (
                    self.transaction_service.get_net_signed_sum_for_account(
                        account_id, day_after_snap, day_before_month
                    )
                )
                balance_at_month_start = base + sum_before
            else:
                oldest = date(1900, 1, 1)
                sum_before = (
                    self.transaction_service.get_net_signed_sum_for_account(
                        account_id, oldest, day_before_month
                    )
                )
                balance_at_month_start = initial + sum_before

            existing = self.balance_snapshot_repository.get_by_account_and_date(
                account_id, month_start
            )
            if not existing:
                snapshot = BalanceSnapshot(
                    account_id=account_id,
                    currency=currency,
                    snapshot_date=month_start,
                    balance=balance_at_month_start,
                )
                self.balance_snapshot_repository.add(snapshot)
                logger.debug(
                    f"Created snapshot for account {account_id} at "
                    f"{month_start} with balance {balance_at_month_start}"
                )

            delta = self.transaction_service.get_net_signed_sum_for_account(
                account_id, month_start, as_of
            )
            return (balance_at_month_start + delta, currency)

    def get_total_balance(
        self, user_id: UUID, as_of: date, base_currency: str
    ) -> Decimal:
        """Total balance across all active accounts as of date, in base currency."""
        accounts_response = self.account_service.get_by_user_id(user_id)
        active = [
            a
            for a in accounts_response.results
            if not getattr(a, "is_deleted", False)
        ]
        total = Decimal("0")
        for acc in active:
            balance_native, currency = self.get_account_balance(acc.id, as_of)
            total += self.fx_service.convert(
                balance_native, currency, base_currency, as_of
            )
        return total

    def get_accounts_balance(
        self, user_id: UUID, as_of: date, base_currency: str
    ) -> tuple[List[dict], Decimal]:
        """
        Balance per account as of a date, converted to base currency.
        Returns (list of account balance dicts, total).
        """
        accounts_response = self.account_service.get_by_user_id(user_id)
        active = [
            a
            for a in accounts_response.results
            if not getattr(a, "is_deleted", False)
        ]
        accounts_list: List[dict] = []
        total_converted = Decimal("0")
        for acc in active:
            balance_native, currency = self.get_account_balance(acc.id, as_of)
            balance_converted = self.fx_service.convert(
                balance_native, currency, base_currency, as_of
            )
            total_converted += balance_converted
            accounts_list.append(
                {
                    "account_id": acc.id,
                    "account_name": acc.name,
                    "currency": currency,
                    "balance_native": balance_native,
                    "balance_converted": balance_converted,
                }
            )
        return (accounts_list, total_converted)

    def get_balance_history(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        period: str,
        account_id: Optional[UUID],
        base_currency: str,
    ) -> List[dict]:
        """
        Balance history for charts or lists. Delegates to BalanceEngine.
        """
        if account_id:
            balance_at_date_fn = lambda d: self.fx_service.convert(
                *self.get_account_balance(account_id, d),
                base_currency,
                d,
            )
        else:
            balance_at_date_fn = lambda d: self.get_total_balance(
                user_id, d, base_currency
            )

        return self.balance_engine.get_balance_history(
            from_date, to_date, period, balance_at_date_fn
        )
