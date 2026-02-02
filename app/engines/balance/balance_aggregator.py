"""
Balance aggregator strategies for balance history.

Each strategy computes balance at a given date - either for a single account
or for all accounts (total).
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.services.account_service import AccountService
    from app.services.balance_service import BalanceService
    from app.services.fx_service import FxService


class BalanceAggregator(ABC):
    """Strategy: what balance to compute at a given date."""

    @abstractmethod
    def compute(self, user_id: UUID, as_of: date, base_currency: str) -> Decimal:
        """Return balance in base currency at as_of."""
        pass


class SingleAccountAggregator(BalanceAggregator):
    """Computes balance for a single account at a date."""

    def __init__(
        self,
        balance_service: "BalanceService",
        fx_service: "FxService",
        account_id: UUID,
    ):
        self.balance_service = balance_service
        self.fx_service = fx_service
        self.account_id = account_id

    def compute(self, user_id: UUID, as_of: date, base_currency: str) -> Decimal:
        bal, currency = self.balance_service.get_account_balance(
            self.account_id, as_of
        )
        return self.fx_service.convert(bal, currency, base_currency, as_of)


class TotalAllAccountsAggregator(BalanceAggregator):
    """Computes total balance across all active accounts at a date."""

    def __init__(
        self,
        balance_service: "BalanceService",
        account_service: "AccountService",
        fx_service: "FxService",
    ):
        self.balance_service = balance_service
        self.account_service = account_service
        self.fx_service = fx_service

    def compute(self, user_id: UUID, as_of: date, base_currency: str) -> Decimal:
        accounts_response = self.account_service.get_by_user_id(user_id)
        active = [
            a
            for a in accounts_response.results
            if not getattr(a, "is_deleted", False)
        ]
        total = Decimal("0")
        for acc in active:
            bal, currency = self.balance_service.get_account_balance(
                acc.id, as_of
            )
            total += self.fx_service.convert(
                bal, currency, base_currency, as_of
            )
        return total
