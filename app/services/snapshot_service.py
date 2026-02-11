"""
Snapshot service: per-account balance at a date using snapshots.

Handles snapshot lookup, lazy creation, and chaining from earlier snapshots.
Returns native balance (account currency). FX conversion is done by BalanceService.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from app.entities.balance_snapshot import BalanceSnapshot
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.services.account_service import AccountService
from app.services.transaction_service import TransactionService
from app.shared.helpers.date_helper import first_day_of_month

logger = logging.getLogger(__name__)


class SnapshotService:
    """
    Manages balance snapshots and computes per-account native balance.

    Uses snapshots for performance. Lazy-creates snapshots when missing.
    Chains from earlier snapshots when possible instead of scanning from 1900.
    """

    def __init__(
        self,
        account_service: AccountService,
        transaction_service: TransactionService,
        balance_snapshot_repository: BalanceSnapshotRepository,
    ):
        self.account_service = account_service
        self.transaction_service = transaction_service
        self.balance_snapshot_repository = balance_snapshot_repository

    def get_account_balance_at(
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

        logger.debug(f"Starting snapshot lookup for account {account_id} as of {as_of}")

        if snap:
            base = Decimal(str(snap.balance))
            snap_date = snap.snapshot_date
            day_after_snap = snap_date + timedelta(days=1)
            delta = self.transaction_service.get_net_signed_sum_for_account(
                account_id, day_after_snap, as_of
            )
            return (base + delta, currency)

        # No snapshot: compute balance at start of month, lazy-create
        day_before_month = month_start - timedelta(days=1)
        snap_before = self.balance_snapshot_repository.get_latest_before(
            account_id, month_start
        )

        if snap_before:
            base = Decimal(str(snap_before.balance))
            day_after_snap = snap_before.snapshot_date + timedelta(days=1)
            sum_before = self.transaction_service.get_net_signed_sum_for_account(
                account_id, day_after_snap, day_before_month
            )
            balance_at_month_start = base + sum_before
        else:
            oldest = date(1900, 1, 1)
            sum_before = self.transaction_service.get_net_signed_sum_for_account(
                account_id, oldest, day_before_month
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
