from datetime import date, timedelta
from typing import Tuple

from app.schemas.reporting_schemas import TransactionSummaryPeriod


def calculate_period_dates(period: TransactionSummaryPeriod) -> Tuple[date, date]:
    """
    Calculate the date range for a given transaction summary period.

    Args:
        period: The period type (day, week, month, year)

    Returns:
        Tuple of (date_from, date_to) where both dates are inclusive
    """
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
        first_day = date(today.year, today.month, 1)
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
