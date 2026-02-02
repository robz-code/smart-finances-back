"""
Period iterator strategies for balance history.

Each strategy yields dates in a range according to a specific granularity
(day, week, month).
"""

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Iterator


class PeriodIterator(ABC):
    """Strategy: how to iterate dates in a range."""

    @abstractmethod
    def iter_dates(self, from_date: date, to_date: date) -> Iterator[date]:
        """Yield dates from from_date to to_date (inclusive) per period."""
        pass


class DayPeriodIterator(PeriodIterator):
    """Yields each day from from_date to to_date."""

    def iter_dates(self, from_date: date, to_date: date) -> Iterator[date]:
        current = from_date
        while current <= to_date:
            yield current
            current += timedelta(days=1)


class WeekPeriodIterator(PeriodIterator):
    """Yields each week from from_date to to_date (step +7 days)."""

    def iter_dates(self, from_date: date, to_date: date) -> Iterator[date]:
        current = from_date
        while current <= to_date:
            yield current
            current += timedelta(days=7)


class MonthPeriodIterator(PeriodIterator):
    """Yields the first day of each month in range."""

    def iter_dates(self, from_date: date, to_date: date) -> Iterator[date]:
        year, month = from_date.year, from_date.month
        end_y, end_m = to_date.year, to_date.month
        while (year, month) <= (end_y, end_m):
            d = date(year, month, 1)
            if d <= to_date:
                yield d
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1
