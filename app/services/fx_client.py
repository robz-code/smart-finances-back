"""
HTTP client for the FastForex currency exchange rate API.

Fetches live exchange rates. Used by FxService for currency conversion.
"""

import logging
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class FxClient:
    """Thin HTTP wrapper around the FastForex API."""

    def __init__(
        self, api_key: str, base_url: str = "https://api.fastforex.io"
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url

    def fetch_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Fetch the exchange rate for a single currency pair.

        Calls: GET /fetch-one?from={from}&to={to}&api_key={key}
        Returns the rate as a Decimal.

        Raises httpx.HTTPStatusError on non-2xx responses.
        """
        url = f"{self._base_url}/fetch-one"
        params = {
            "from": from_currency,
            "to": to_currency,
            "api_key": self._api_key,
        }

        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        rate = data["result"][to_currency]
        logger.debug("FX rate fetched: %s/%s = %s", from_currency, to_currency, rate)
        return Decimal(str(rate))
