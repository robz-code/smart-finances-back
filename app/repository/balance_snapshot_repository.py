"""
Repository for balance_snapshots.

Snapshots are a reporting optimization: balance at start of month, in account currency.
They are lazy-created and rebuildable; never store converted balances.
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.balance_snapshot import BalanceSnapshot
from app.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class BalanceSnapshotRepository(BaseRepository[BalanceSnapshot]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, BalanceSnapshot)

    def get_by_account_and_date(
        self, account_id: UUID, snapshot_date: date
    ) -> Optional[BalanceSnapshot]:
        """Get snapshot for account on exact snapshot_date (should be first day of month)."""
        logger.debug(
            f"DB get_by_account_and_date: BalanceSnapshot account_id={account_id} snapshot_date={snapshot_date}"
        )
        return (
            self.db.query(BalanceSnapshot)
            .filter(
                BalanceSnapshot.account_id == account_id,
                BalanceSnapshot.snapshot_date == snapshot_date,
            )
            .first()
        )

    def get_latest_before(
        self, account_id: UUID, before_date: date
    ) -> Optional[BalanceSnapshot]:
        """
        Get the latest snapshot for account where snapshot_date < before_date.
        Used to chain from an earlier snapshot instead of scanning from 1900.
        """
        logger.debug(
            f"DB get_latest_before: BalanceSnapshot account_id={account_id} before_date={before_date}"
        )
        return (
            self.db.query(BalanceSnapshot)
            .filter(
                BalanceSnapshot.account_id == account_id,
                BalanceSnapshot.snapshot_date < before_date,
            )
            .order_by(BalanceSnapshot.snapshot_date.desc())
            .first()
        )

    def get_latest_before_or_on(
        self, account_id: UUID, as_of: date
    ) -> Optional[BalanceSnapshot]:
        """
        Get the latest snapshot for account where snapshot_date <= as_of.
        Used to compute balance(as_of) = snapshot_balance + transactions(snapshot_date, as_of].
        """
        logger.debug(
            f"DB get_latest_before_or_on: BalanceSnapshot account_id={account_id} as_of={as_of}"
        )
        return (
            self.db.query(BalanceSnapshot)
            .filter(
                BalanceSnapshot.account_id == account_id,
                BalanceSnapshot.snapshot_date <= as_of,
            )
            .order_by(BalanceSnapshot.snapshot_date.desc())
            .first()
        )

    def delete_future_snapshots(self, account_id: UUID, from_date: date) -> int:
        """
        Delete snapshots for account where snapshot_date >= from_date.
        Call this when a transaction is edited or deleted so future snapshots
        are invalidated and will be rebuilt lazily.
        """
        logger.debug(
            f"DB delete_future_snapshots: BalanceSnapshot account_id={account_id} from_date={from_date}"
        )
        from app.entities.balance_snapshot import BalanceSnapshot as BS

        deleted = (
            self.db.query(BS)
            .filter(BS.account_id == account_id, BS.snapshot_date >= from_date)
            .delete(synchronize_session=False)
        )
        # Caller is responsible for commit (e.g. same request as transaction update/delete)
        return deleted
