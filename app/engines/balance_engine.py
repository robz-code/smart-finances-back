"""
Balance engine: balance reporting computations (O(1) queries, N+1 safe).

This engine owns the balance algorithms and uses set-based repository methods.
It is not FastAPI-aware: no schemas, no HTTP exceptions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.entities.balance_snapshot import BalanceSnapshot
from app.repository.account_repository import AccountRepository
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository
from app.repository.transaction_repository import TransactionRepository
from app.services.fx_service import FxService
from app.shared.helpers.date_helper import first_day_of_month, iter_dates


class BalanceEngine:
    """Computes balances using snapshots + transactions and converts at read time."""

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

    # ---------------------------------------------------------------------
    # Public API (used by ReportingService)
    # ---------------------------------------------------------------------

    def get_total_balance(
        self, user_id: UUID, as_of: date, base_currency: str
    ) -> Decimal:
        accounts = self._load_accounts(user_id=user_id)
        if not accounts:
            return Decimal("0")

        native_balances = self._compute_native_balances_as_of(
            accounts=accounts,
            as_of=as_of,
        )

        total = Decimal("0")
        for acc in accounts:
            native = native_balances.get(acc.id, Decimal("0"))
            total += self.fx_service.convert(
                native, acc.currency, base_currency, as_of
            )
        return total

    def get_accounts_balance(
        self, user_id: UUID, as_of: date, base_currency: str
    ) -> tuple[List[dict], Decimal]:
        accounts = self._load_accounts(user_id=user_id)
        if not accounts:
            return ([], Decimal("0"))

        native_balances = self._compute_native_balances_as_of(
            accounts=accounts,
            as_of=as_of,
        )

        accounts_list: List[dict] = []
        total_converted = Decimal("0")
        for acc in accounts:
            native = native_balances.get(acc.id, Decimal("0"))
            converted = self.fx_service.convert(
                native, acc.currency, base_currency, as_of
            )
            total_converted += converted
            accounts_list.append(
                {
                    "account_id": acc.id,
                    "account_name": acc.name,
                    "currency": acc.currency,
                    "balance_native": native,
                    "balance_converted": converted,
                }
            )
        return (accounts_list, total_converted)

    def get_balance_history(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        period: str,
        base_currency: str,
        *,
        account_id: Optional[UUID] = None,
    ) -> List[dict]:
        accounts = self._load_accounts(user_id=user_id, account_id_filter=account_id)
        if not accounts:
            return [
                {"date": d.isoformat(), "balance": Decimal("0")}
                for d in iter_dates(from_date, to_date, period)
            ]

        account_ids = [a.id for a in accounts]
        month_start_from = first_day_of_month(from_date)

        snapshots = self.snapshot_repo.get_latest_snapshots_for_accounts(
            account_ids, month_start_from
        )
        snap_before_map = self.snapshot_repo.get_latest_before_for_accounts(
            account_ids, month_start_from
        )
        tx_rows = self.transaction_repo.get_transactions_for_accounts_until_date(
            account_ids, to_date
        )

        tx_before_by_account: Dict[UUID, List[tuple]] = defaultdict(list)
        tx_by_date: Dict[date, List[tuple]] = defaultdict(list)
        for acc_id, tx_date, amount in tx_rows:
            if tx_date < from_date:
                tx_before_by_account[acc_id].append((tx_date, amount))
            elif from_date <= tx_date <= to_date:
                tx_by_date[tx_date].append((acc_id, amount))

        balances = self._compute_initial_balances(
            accounts=accounts,
            from_date=from_date,
            snapshots=snapshots,
            snap_before_map=snap_before_map,
            tx_before_by_account=tx_before_by_account,
        )

        points: List[dict] = []
        sorted_tx_dates = sorted(tx_by_date.keys())
        tx_index = 0

        for d in iter_dates(from_date, to_date, period):
            while tx_index < len(sorted_tx_dates) and sorted_tx_dates[tx_index] <= d:
                tx_day = sorted_tx_dates[tx_index]
                for acc_id, amt in tx_by_date[tx_day]:
                    balances[acc_id] = balances.get(acc_id, Decimal("0")) + amt
                tx_index += 1

            total = Decimal("0")
            for acc in accounts:
                b = balances.get(acc.id, Decimal("0"))
                total += self.fx_service.convert(b, acc.currency, base_currency, d)
            points.append({"date": d.isoformat(), "balance": total})

        return points

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _load_accounts(
        self, *, user_id: UUID, account_id_filter: Optional[UUID] = None
    ) -> List:
        all_accounts = self.account_repo.get_by_user_id(user_id)
        active = [a for a in all_accounts if not getattr(a, "is_deleted", False)]
        if account_id_filter:
            active = [a for a in active if a.id == account_id_filter]
        return active

    def _compute_native_balances_as_of(
        self,
        *,
        accounts: List,
        as_of: date,
    ) -> Dict[UUID, Decimal]:
        account_ids = [a.id for a in accounts]

        snapshots = self.snapshot_repo.get_latest_snapshots_for_accounts(
            account_ids, as_of
        )
        tx_rows = self.transaction_repo.get_transactions_for_accounts_until_date(
            account_ids, as_of
        )

        month_start = first_day_of_month(as_of)
        day_before_month = month_start - timedelta(days=1)

        tx_by_account: Dict[UUID, List[tuple]] = defaultdict(list)
        for acc_id, tx_date, amount in tx_rows:
            tx_by_account[acc_id].append((tx_date, amount))

        accounts_without_snap = [
            acc for acc in accounts if snapshots.get(acc.id) is None
        ]
        snap_before_map: Dict[UUID, Optional[BalanceSnapshot]] = {}
        existing_at_month: Dict[UUID, Optional[BalanceSnapshot]] = {}
        if accounts_without_snap:
            ids_without = [a.id for a in accounts_without_snap]
            snap_before_map = self.snapshot_repo.get_latest_before_for_accounts(
                ids_without, month_start
            )
            existing_at_month = self.snapshot_repo.get_snapshots_at_date(
                ids_without, month_start
            )

        result: Dict[UUID, Decimal] = {}
        to_create: List[BalanceSnapshot] = []

        for acc in accounts:
            currency = acc.currency
            initial = Decimal(str(acc.initial_balance or 0))
            snap = snapshots.get(acc.id)

            account_txs = tx_by_account.get(acc.id, [])

            if snap:
                base = Decimal(str(snap.balance))
                day_after_snap = snap.snapshot_date + timedelta(days=1)
                delta = sum(
                    amt
                    for d, amt in account_txs
                    if day_after_snap <= d <= as_of
                )
                result[acc.id] = base + delta
                continue

            snap_before = snap_before_map.get(acc.id)

            if snap_before:
                base = Decimal(str(snap_before.balance))
                day_after_snap = snap_before.snapshot_date + timedelta(days=1)
                sum_before = sum(
                    amt
                    for d, amt in account_txs
                    if day_after_snap <= d <= day_before_month
                )
                balance_at_month_start = base + sum_before
            else:
                sum_before = sum(amt for d, amt in account_txs if d <= day_before_month)
                balance_at_month_start = initial + sum_before

            if acc.id not in existing_at_month or existing_at_month[acc.id] is None:
                to_create.append(
                    BalanceSnapshot(
                        account_id=acc.id,
                        currency=currency,
                        snapshot_date=month_start,
                        balance=balance_at_month_start,
                    )
                )

            delta = sum(amt for d, amt in account_txs if month_start <= d <= as_of)
            result[acc.id] = balance_at_month_start + delta

        if to_create:
            self.snapshot_repo.add_many(to_create)

        return result

    def _compute_initial_balances(
        self,
        *,
        accounts: List,
        from_date: date,
        snapshots: Dict[UUID, Optional[BalanceSnapshot]],
        snap_before_map: Dict[UUID, Optional[BalanceSnapshot]],
        tx_before_by_account: Dict[UUID, List[tuple]],
    ) -> Dict[UUID, Decimal]:
        result: Dict[UUID, Decimal] = {}
        day_before_from = from_date - timedelta(days=1)

        for acc in accounts:
            initial = Decimal(str(acc.initial_balance or 0))
            account_txs = tx_before_by_account.get(acc.id, [])
            snap = snapshots.get(acc.id)
            snap_before = snap_before_map.get(acc.id)

            if snap:
                base = Decimal(str(snap.balance))
                day_after_snap = snap.snapshot_date + timedelta(days=1)
                delta = sum(
                    amt
                    for d, amt in account_txs
                    if day_after_snap <= d <= day_before_from
                )
                result[acc.id] = base + delta
            elif snap_before:
                base = Decimal(str(snap_before.balance))
                day_after_snap = snap_before.snapshot_date + timedelta(days=1)
                delta = sum(
                    amt
                    for d, amt in account_txs
                    if day_after_snap <= d <= day_before_from
                )
                result[acc.id] = base + delta
            else:
                delta = sum(amt for d, amt in account_txs if d <= day_before_from)
                result[acc.id] = initial + delta

        return result
