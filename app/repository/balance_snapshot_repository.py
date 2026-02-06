"""
Repository for balance_snapshots.

Snapshots are a reporting optimization: balance at start of month, in account currency.
They are lazy-created and rebuildable; never store converted balances.

All methods are set-based; never call inside loops.
"""

import logging
from datetime import date
from typing import Dict, List, Optional
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

    def get_latest_snapshots_for_accounts(
        self, account_ids: List[UUID], as_of: date
    ) -> Dict[UUID, Optional[BalanceSnapshot]]:
        """
        Get latest snapshot (snapshot_date <= as_of) for each account in one query.

        Returns dict mapping account_id to snapshot, or None if no snapshot exists.
        """
        if not account_ids:
            return {}
        logger.debug(
            f"DB get_latest_snapshots_for_accounts: account_ids={len(account_ids)} "
            f"as_of={as_of}"
        )
        # Use DISTINCT ON (Postgres) or subquery for "latest per account"
        # SQLite doesn't support DISTINCT ON; use a correlated subquery or group by
        subq = (
            self.db.query(BalanceSnapshot)
            .filter(
                BalanceSnapshot.account_id.in_(account_ids),
                BalanceSnapshot.snapshot_date <= as_of,
            )
            .order_by(
                BalanceSnapshot.account_id,
                BalanceSnapshot.snapshot_date.desc(),
            )
        )
        rows = subq.all()
        # Deduplicate: keep first (latest) per account
        result: Dict[UUID, Optional[BalanceSnapshot]] = {
            aid: None for aid in account_ids
        }
        seen: set = set()
        for row in rows:
            if row.account_id not in seen:
                seen.add(row.account_id)
                result[row.account_id] = row
        return result

    def get_latest_before_for_accounts(
        self, account_ids: List[UUID], before_date: date
    ) -> Dict[UUID, Optional[BalanceSnapshot]]:
        """
        Get latest snapshot (snapshot_date < before_date) for each account in one query.
        """
        if not account_ids:
            return {}
        logger.debug(
            f"DB get_latest_before_for_accounts: account_ids={len(account_ids)} "
            f"before_date={before_date}"
        )
        rows = (
            self.db.query(BalanceSnapshot)
            .filter(
                BalanceSnapshot.account_id.in_(account_ids),
                BalanceSnapshot.snapshot_date < before_date,
            )
            .order_by(
                BalanceSnapshot.account_id,
                BalanceSnapshot.snapshot_date.desc(),
            )
            .all()
        )
        result: Dict[UUID, Optional[BalanceSnapshot]] = {
            aid: None for aid in account_ids
        }
        seen: set = set()
        for row in rows:
            if row.account_id not in seen:
                seen.add(row.account_id)
                result[row.account_id] = row
        return result

    def get_snapshots_at_date(
        self, account_ids: List[UUID], snapshot_date: date
    ) -> Dict[UUID, Optional[BalanceSnapshot]]:
        """Get snapshot for each account at exact snapshot_date (e.g. month start)."""
        if not account_ids:
            return {}
        logger.debug(
            f"DB get_snapshots_at_date: account_ids={len(account_ids)} "
            f"snapshot_date={snapshot_date}"
        )
        rows = (
            self.db.query(BalanceSnapshot)
            .filter(
                BalanceSnapshot.account_id.in_(account_ids),
                BalanceSnapshot.snapshot_date == snapshot_date,
            )
            .all()
        )
        return {r.account_id: r for r in rows}

    def add_many(self, snapshots: List[BalanceSnapshot]) -> None:
        """Batch insert snapshots. Caller must commit."""
        if not snapshots:
            return
        logger.debug(f"DB add_many: BalanceSnapshot count={len(snapshots)}")
        for s in snapshots:
            self.db.add(s)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

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
