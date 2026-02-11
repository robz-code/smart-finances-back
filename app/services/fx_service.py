"""
FX (foreign exchange) conversion for reporting.

CORE FINANCIAL PRINCIPLE:
FX conversion is a presentation concern. It happens at read time only, using the as_of date.
It never mutates the ledger or snapshots. Balances are stored in account currency;
conversion to user base currency is done here when returning reporting data.
"""

from datetime import date
from decimal import Decimal


class FxService:
    """
    FX conversion at read time (presentation concern only).

    MVP implementation: hard-coded rates + passthrough fallback.
    """

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        as_of: date,
    ) -> Decimal:
        """
        Convert amount from from_currency to to_currency using rates as of as_of date.
        Used only for presentation; never mutates ledger or snapshots.
        """
        if from_currency == to_currency:
            return amount
        if from_currency == "USD" and to_currency == "MXN":
            return amount * Decimal(17.5)
        elif from_currency == "MXN" and to_currency == "USD":
            return amount * Decimal(0.057)
        elif from_currency == "USD" and to_currency == "EUR":
            return amount * Decimal(1.10)
        elif from_currency == "EUR" and to_currency == "USD":
            return amount * Decimal(0.90)
        elif from_currency == "MXN" and to_currency == "EUR":
            return amount * Decimal(0.050)
        elif from_currency == "EUR" and to_currency == "MXN":
            return amount * Decimal(20.00)
        # Unknown pair: keep behavior safe and deterministic for MVP.
        return amount
