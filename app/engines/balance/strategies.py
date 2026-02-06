"""
Concrete balance strategies: batch-load data, compute in memory.

Each strategy performs O(1) database queries. No DB calls inside loops.
"""

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
from app.shared.helpers.date_helper import first_day_of_month


class TotalBalanceAtDateStrategy:
    """
    Strategy for GET /balance: total balance as of a date in base currency.

    Batch-loads: accounts, snapshots, transactions. Computes in memory.
    """

    def __init__(
        self,
        user_id: UUID,
        as_of: date,
        base_currency: str,
        account_repo: AccountRepository,
        snapshot_repo: BalanceSnapshotRepository,
        transaction_repo: TransactionRepository,
        fx_service: FxService,
    ):
        self.user_id = user_id
        self.as_of = as_of
        self.base_currency = base_currency
        self.account_repo = account_repo
        self.snapshot_repo = snapshot_repo
        self.transaction_repo = transaction_repo
        self.fx_service = fx_service

    def execute(self) -> Decimal:
        accounts = self._load_accounts()
        if not accounts:
            return Decimal("0")

        account_ids = [a.id for a in accounts]

        snapshots = self.snapshot_repo.get_latest_snapshots_for_accounts(
            account_ids, self.as_of
        )
        tx_rows = self.transaction_repo.get_transactions_for_accounts_until_date(
            account_ids, self.as_of
        )

        native_balances = self._compute_native_balances(
            accounts, snapshots, tx_rows
        )

        total = Decimal("0")
        for acc in accounts:
            native = native_balances.get(acc.id, Decimal("0"))
            total += self.fx_service.convert(
                native, acc.currency, self.base_currency, self.as_of
            )
        return total

    def _load_accounts(self) -> List:
        all_accounts = self.account_repo.get_by_user_id(self.user_id)
        return [a for a in all_accounts if not getattr(a, "is_deleted", False)]

    def _compute_native_balances(
        self,
        accounts: List,
        snapshots: Dict[UUID, Optional[BalanceSnapshot]],
        tx_rows: List[tuple],
    ) -> Dict[UUID, Decimal]:
        month_start = first_day_of_month(self.as_of)
        day_before_month = month_start - timedelta(days=1)
        result: Dict[UUID, Decimal] = {}

        tx_by_account: Dict[UUID, List[tuple]] = defaultdict(list)
        for acc_id, tx_date, amount in tx_rows:
            tx_by_account[acc_id].append((tx_date, amount))

        accounts_without_snap = [acc for acc in accounts if snapshots.get(acc.id) is None]
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
                    amt for d, amt in account_txs
                    if day_after_snap <= d <= self.as_of
                )
                result[acc.id] = base + delta
                continue

            snap_before = snap_before_map.get(acc.id)

            if snap_before:
                base = Decimal(str(snap_before.balance))
                day_after_snap = snap_before.snapshot_date + timedelta(days=1)
                sum_before = sum(
                    amt for d, amt in account_txs
                    if day_after_snap <= d <= day_before_month
                )
                balance_at_month_start = base + sum_before
            else:
                sum_before = sum(
                    amt for d, amt in account_txs if d <= day_before_month
                )
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

            delta = sum(
                amt for d, amt in account_txs
                if month_start <= d <= self.as_of
            )
            result[acc.id] = balance_at_month_start + delta

        if to_create:
            self.snapshot_repo.add_many(to_create)

        return result


class PerAccountBalanceAtDateStrategy:
    """
    Strategy for GET /balance/accounts: per-account balances as of a date.

    Reuses same data-loading as TotalBalanceAtDateStrategy.
    Returns (accounts_list, total).
    """

    def __init__(
        self,
        user_id: UUID,
        as_of: date,
        base_currency: str,
        account_repo: AccountRepository,
        snapshot_repo: BalanceSnapshotRepository,
        transaction_repo: TransactionRepository,
        fx_service: FxService,
    ):
        self.user_id = user_id
        self.as_of = as_of
        self.base_currency = base_currency
        self.account_repo = account_repo
        self.snapshot_repo = snapshot_repo
        self.transaction_repo = transaction_repo
        self.fx_service = fx_service

    def execute(self) -> tuple:
        total_strategy = TotalBalanceAtDateStrategy(
            self.user_id,
            self.as_of,
            self.base_currency,
            self.account_repo,
            self.snapshot_repo,
            self.transaction_repo,
            self.fx_service,
        )
        accounts = total_strategy._load_accounts()
        if not accounts:
            return ([], Decimal("0"))

        account_ids = [a.id for a in accounts]
        snapshots = self.snapshot_repo.get_latest_snapshots_for_accounts(
            account_ids, self.as_of
        )
        tx_rows = self.transaction_repo.get_transactions_for_accounts_until_date(
            account_ids, self.as_of
        )
        native_balances = total_strategy._compute_native_balances(
            accounts, snapshots, tx_rows
        )

        accounts_list: List[dict] = []
        total_converted = Decimal("0")
        for acc in accounts:
            native = native_balances.get(acc.id, Decimal("0"))
            converted = self.fx_service.convert(
                native, acc.currency, self.base_currency, self.as_of
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


class BalanceHistoryStrategy:
    """
    Strategy for GET /balance/history: balance over time.

    Loads accounts once, snapshots once, all transactions until to_date once.
    Walks forward in memory applying transactions incrementally.
    """

    def __init__(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        period: str,
        base_currency: str,
        account_id: Optional[UUID],
        account_repo: AccountRepository,
        snapshot_repo: BalanceSnapshotRepository,
        transaction_repo: TransactionRepository,
        fx_service: FxService,
        period_iterator,
    ):
        self.user_id = user_id
        self.from_date = from_date
        self.to_date = to_date
        self.period = period
        self.base_currency = base_currency
        self.account_id_filter = account_id
        self.account_repo = account_repo
        self.snapshot_repo = snapshot_repo
        self.transaction_repo = transaction_repo
        self.fx_service = fx_service
        self.period_iterator = period_iterator

    def execute(self) -> List[dict]:
        accounts = self._load_accounts()
        if not accounts:
            return [
                {"date": d.isoformat(), "balance": Decimal("0")}
                for d in self.period_iterator.iter_dates(self.from_date, self.to_date)
            ]

        account_ids = [a.id for a in accounts]

        month_start_from = first_day_of_month(self.from_date)
        snapshots = self.snapshot_repo.get_latest_snapshots_for_accounts(
            account_ids, month_start_from
        )
        snap_before_map = self.snapshot_repo.get_latest_before_for_accounts(
            account_ids, month_start_from
        )
        tx_rows = self.transaction_repo.get_transactions_for_accounts_until_date(
            account_ids, self.to_date
        )

        tx_before_by_account: Dict[UUID, List[tuple]] = defaultdict(list)
        tx_by_date: Dict[date, List[tuple]] = defaultdict(list)
        for acc_id, tx_date, amount in tx_rows:
            if tx_date < self.from_date:
                tx_before_by_account[acc_id].append((tx_date, amount))
            elif self.from_date <= tx_date <= self.to_date:
                tx_by_date[tx_date].append((acc_id, amount))

        initial_balances = self._compute_initial_balances(
            accounts, snapshots, snap_before_map, tx_before_by_account
        )

        points: List[dict] = []
        balances = dict(initial_balances)
        sorted_tx_dates = sorted(tx_by_date.keys())
        tx_index = 0

        for d in self.period_iterator.iter_dates(self.from_date, self.to_date):
            while tx_index < len(sorted_tx_dates) and sorted_tx_dates[tx_index] <= d:
                tx_day = sorted_tx_dates[tx_index]
                for acc_id, amt in tx_by_date[tx_day]:
                    balances[acc_id] = balances.get(acc_id, Decimal("0")) + amt
                tx_index += 1
            total = Decimal("0")
            for acc in accounts:
                b = balances.get(acc.id, Decimal("0"))
                total += self.fx_service.convert(
                    b, acc.currency, self.base_currency, d
                )
            points.append({"date": d.isoformat(), "balance": total})

        return points

    def _load_accounts(self) -> List:
        all_accounts = self.account_repo.get_by_user_id(self.user_id)
        active = [a for a in all_accounts if not getattr(a, "is_deleted", False)]
        if self.account_id_filter:
            active = [a for a in active if a.id == self.account_id_filter]
        return active

    def _compute_initial_balances(
        self,
        accounts: List,
        snapshots: Dict[UUID, Optional[BalanceSnapshot]],
        snap_before_map: Dict[UUID, Optional[BalanceSnapshot]],
        tx_before_by_account: Dict[UUID, List[tuple]],
    ) -> Dict[UUID, Decimal]:
        result: Dict[UUID, Decimal] = {}
        day_before_from = self.from_date - timedelta(days=1)
        month_start = first_day_of_month(self.from_date)

        for acc in accounts:
            initial = Decimal(str(acc.initial_balance or 0))
            account_txs = tx_before_by_account.get(acc.id, [])
            snap = snapshots.get(acc.id)
            snap_before = snap_before_map.get(acc.id)

            if snap:
                base = Decimal(str(snap.balance))
                day_after_snap = snap.snapshot_date + timedelta(days=1)
                delta = sum(
                    amt for d, amt in account_txs if day_after_snap <= d <= day_before_from
                )
                result[acc.id] = base + delta
            elif snap_before:
                base = Decimal(str(snap_before.balance))
                day_after_snap = snap_before.snapshot_date + timedelta(days=1)
                delta = sum(
                    amt for d, amt in account_txs if day_after_snap <= d <= day_before_from
                )
                result[acc.id] = base + delta
            else:
                delta = sum(amt for d, amt in account_txs if d <= day_before_from)
                result[acc.id] = initial + delta

        return result
