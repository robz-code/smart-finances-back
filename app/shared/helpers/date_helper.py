from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Iterator, Tuple

if TYPE_CHECKING:
    from app.schemas.reporting_schemas import TransactionSummaryPeriod


def first_day_of_month(d: date) -> date:
    """First day of the month for date d (snapshots are always at month start)."""
    return d.replace(day=1)


def iter_dates(from_date: date, to_date: date, period: str) -> Iterator[date]:
    """
    Yield dates from from_date to to_date (inclusive) following the given period.

    period:
      - "day": yields every day
      - "week": yields every 7 days starting at from_date
      - "month": yields the first day of each month, but never before from_date
    """
    if from_date > to_date:
        return

    if period == "day":
        current = from_date
        while current <= to_date:
            yield current
            current += timedelta(days=1)
        return

    if period == "week":
        current = from_date
        while current <= to_date:
            yield current
            current += timedelta(days=7)
        return

    if period == "month":
        # Start at the first-of-month for from_date, but never yield a point
        # before from_date itself (e.g. from_date=2026-02-15 should start at 2026-03-01).
        year, month = from_date.year, from_date.month
        current = date(year, month, 1)
        if current < from_date:
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1
            current = date(year, month, 1)

        while current <= to_date:
            yield current
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        return

    raise ValueError(f"period must be one of: day, week, month (got {period})")


def calculate_period_dates(period: TransactionSummaryPeriod) -> Tuple[date, date]:
    """
    Calculate the date range for a given transaction summary period.

    Args:
        period: The period type (day, week, month, year)

    Returns:
        Tuple of (date_from, date_to) where both dates are inclusive
    """
    # Local import to keep this module usable from engines/services without
    # pulling reporting schema types at import time.
    from app.schemas.reporting_schemas import TransactionSummaryPeriod

    today = date.today()

    if period == TransactionSummaryPeriod.DAY:
        return (today, today)

    elif period == TransactionSummaryPeriod.WEEK:
        # Get Monday of current week
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        # Get Sunday of current week
        sunday = monday + timedelta(days=6)
        return (monday, sunday)

    elif period == TransactionSummaryPeriod.MONTH:
        # First day of current month
        first_day = first_day_of_month(today)
        # Last day of current month
        if today.month == 12:
            last_day = date(today.year, 12, 31)
        else:
            last_day = date(today.year, today.month + 1, 1) - timedelta(days=1)
        return (first_day, last_day)

    elif period == TransactionSummaryPeriod.YEAR:
        # January 1st of current year
        first_day = date(today.year, 1, 1)
        # December 31st of current year
        last_day = date(today.year, 12, 31)
        return (first_day, last_day)

    else:
        raise ValueError(f"Unknown period: {period}")
