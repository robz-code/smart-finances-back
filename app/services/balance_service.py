"""
Balance service: per-account balance, totals, and history.

Uses SnapshotService for per-account balance. FX conversion and aggregation.
Delegates complex history iteration to BalanceEngine.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.engines.balance_engine import BalanceEngine
from app.services.account_service import AccountService
from app.services.fx_service import FxService
from app.services.snapshot_service import SnapshotService


class BalanceService:
    """
    Balance domain service. Per-account balance, totals, history.

    Uses SnapshotService for per-account native balance, FxService for
    conversion, BalanceEngine for history iteration.
    """

    def __init__(
        self,
        account_service: AccountService,
        snapshot_service: SnapshotService,
        fx_service: FxService,
        balance_engine: BalanceEngine,
    ):
        self.account_service = account_service
        self.snapshot_service = snapshot_service
        self.fx_service = fx_service
        self.balance_engine = balance_engine

    def get_account_balance(
        self, account_id: UUID, as_of: date
    ) -> tuple[Decimal, str]:
        """Native balance for one account at date. Delegates to SnapshotService."""
        return self.snapshot_service.get_account_balance_at(account_id, as_of)

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
        """Balance history for charts or lists. Delegates to BalanceEngine."""
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

        return self.balance_engine.get_balance_history_from_callback(
            from_date, to_date, period, balance_at_date_fn
        )
