"""
FX (foreign exchange) conversion for reporting.

CORE FINANCIAL PRINCIPLE:
FX conversion is a presentation concern. It happens at read time only, using the as_of date.
It never mutates the ledger or snapshots. Balances are stored in account currency;
conversion to user base currency is done here when returning reporting data.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Dict, Optional, Tuple

from app.services.fx_client import FxClient

logger = logging.getLogger(__name__)

# Type alias for the rate cache key: (from_currency, to_currency)
_CacheKey = Tuple[str, str]


class FxService:
    """
    FX conversion at read time (presentation concern only).

    Fetches live rates from FastForex via FxClient and caches them
    for the lifetime of the service instance (i.e. per-request).
    """

    def __init__(self, fx_client: Optional[FxClient] = None) -> None:
        self._client = fx_client
        self._cache: Dict[_CacheKey, Decimal] = {}

    def _get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Get the rate for a pair, using in-memory cache to avoid duplicate calls."""
        key: _CacheKey = (from_currency, to_currency)
        if key not in self._cache:
            if self._client is None:
                logger.warning(
                    "No FX client configured; returning 1:1 for %s→%s",
                    from_currency,
                    to_currency,
                )
                return Decimal("1")
            self._cache[key] = self._client.fetch_rate(from_currency, to_currency)
            logger.info(
                "FX rate cached: %s→%s = %s",
                from_currency,
                to_currency,
                self._cache[key],
            )
        else:
            logger.info(
                "FX rate cache hit: %s→%s = %s",
                from_currency,
                to_currency,
                self._cache[key],
            )
        return self._cache[key]

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        as_of: date,
    ) -> Decimal:
        """
        Convert amount from from_currency to to_currency.
        Used only for presentation; never mutates ledger or snapshots.
        """
        if from_currency == to_currency:
            logger.info(
                "FX convert: same currency %s, no conversion needed (amount=%s)",
                from_currency,
                amount,
            )
            return amount

        # as_of reserved for historical rate support (FastForex historical endpoint).
        _ = as_of
        rate = self._get_rate(from_currency, to_currency)
        converted = amount * rate
        logger.info(
            "FX convert: %s %s → %s %s (rate=%s, as_of=%s)",
            amount,
            from_currency,
            converted,
            to_currency,
            rate,
            as_of,
        )
        return converted
