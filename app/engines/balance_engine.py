"""
Balance engine: complex logic for balance history computation.

Uses PeriodIterator strategies and a callback pattern to avoid circular
dependencies. BalanceService creates the balance_at_date_fn and passes it.
"""

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import List

from app.engines.balance.period_iterator import (
    DayPeriodIterator,
    MonthPeriodIterator,
    WeekPeriodIterator,
)


class BalanceEngine:
    """
    Engine for balance history computation.

    Stateless; receives a balance_at_date_fn callback from BalanceService.
    Iterates dates per period and calls the callback for each date.
    """

    PERIOD_ITERATORS = {
        "day": DayPeriodIterator(),
        "week": WeekPeriodIterator(),
        "month": MonthPeriodIterator(),
    }

    def get_balance_history(
        self,
        from_date: date,
        to_date: date,
        period: str,
        balance_at_date_fn: Callable[[date], Decimal],
    ) -> List[dict]:
        """
        Compute balance history for charts or lists.

        Args:
            from_date: Start date (inclusive)
            to_date: End date (inclusive)
            period: Granularity - "day", "week", or "month"
            balance_at_date_fn: Callable that returns balance in base currency
                for a given date. Provided by BalanceService.

        Returns:
            List of {"date": iso_str, "balance": Decimal}
        """
        iterator = self.PERIOD_ITERATORS.get(period)
        if not iterator:
            raise ValueError(
                f"period must be one of: day, week, month (got {period})"
            )

        points: List[dict] = []
        for d in iterator.iter_dates(from_date, to_date):
            converted = balance_at_date_fn(d)
            points.append({"date": d.isoformat(), "balance": converted})
        return points
