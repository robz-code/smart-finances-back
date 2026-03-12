"""
HTTP client for the ExchangeRate-API currency exchange rate API.

Fetches live exchange rates. Used by FxService for currency conversion.
"""

import logging
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class FxClient:
    """Thin HTTP wrapper around the ExchangeRate-API v6."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://v6.exchangerate-api.com/v6",
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url

    def fetch_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Fetch the exchange rate for a single currency pair.

        Calls: GET /v6/{api_key}/pair/{from}/{to}
        Returns the rate as a Decimal.

        Raises httpx.HTTPStatusError on non-2xx responses.
        """
        url = f"{self._base_url}/{self._api_key}/pair/{from_currency}/{to_currency}"

        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        rate = data["conversion_rate"]
        logger.debug("FX rate fetched: %s/%s = %s", from_currency, to_currency, rate)
        return Decimal(str(rate))
