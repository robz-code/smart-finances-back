from datetime import date as Date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import UUID4, BaseModel, Field, model_validator

from app.entities.category import CategoryType
from app.entities.transaction import TransactionType


class TransactionSummaryPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


# Balance history supports day/week/month only (year not supported)
BALANCE_HISTORY_PERIODS = {
    TransactionSummaryPeriod.DAY,
    TransactionSummaryPeriod.WEEK,
    TransactionSummaryPeriod.MONTH,
}


class ReportingParameters(BaseModel):
    """Query parameters for reporting endpoints. Use either period OR date_from/date_to."""

    model_config = {"populate_by_name": True}

    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    type: Optional[str] = Field(default=None, alias="type")
    currency: Optional[str] = None
    date_from: Optional[Date] = None
    date_to: Optional[Date] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    source: Optional[str] = None
    period: Optional[TransactionSummaryPeriod] = None
    full_list: bool = Field(
        default=True,
        description="If True, include all categories (including those with 0 transactions). If False, only return categories that have matching transactions.",
    )

    @model_validator(mode="after")
    def ensure_date_range_or_period(self) -> "ReportingParameters":
        """Ensure either period is set OR both date_from and date_to. Period takes precedence."""
        if self.period is not None:
            # Period is set: ignore date filters (don't use them)
            return self
        # Period not set: require both date_from and date_to
        if self.date_from is None or self.date_to is None:
            raise ValueError(
                "Either 'period' or both 'date_from' and 'date_to' must be provided"
            )
        if self.date_from > self.date_to:
            raise ValueError("'date_from' must be before or equal to 'date_to'")
        return self


class CategoryAggregationData(BaseModel):
    """DTO for category transaction aggregation data"""

    net_signed_amount: Decimal
    transaction_count: int


class CategorySummaryResponse(BaseModel):
    id: UUID4
    name: str
    type: CategoryType
    icon: Optional[str] = None
    color: Optional[str] = None
    transaction_amount: Decimal
    transaction_count: int

    model_config = {
        "json_encoders": {
            Decimal: lambda v: format(v, ".2f")  # Format to 2 decimal places in JSON
        }
    }


class CashflowSummaryResponse(BaseModel):
    """Income, expense, and net total for a period."""

    income: Decimal
    expense: Decimal
    total: Decimal

    model_config = {
        "json_encoders": {
            Decimal: lambda v: format(v, ".2f")  # Format to 2 decimal places in JSON
        }
    }


class CashflowHistoryPoint(BaseModel):
    """One point in historical cashflow series."""

    period_start: str  # YYYY-MM-DD
    income: Decimal
    expense: Decimal
    net: Decimal

    model_config = {
        "json_encoders": {
            Decimal: lambda v: format(v, ".2f"),
        }
    }


class CashflowHistoryResponse(BaseModel):
    """Historical cashflow response by period."""

    period: str
    date_from: Date
    date_to: Date
    currency: str
    points: list[CashflowHistoryPoint]

    model_config = {
        "json_encoders": {
            Decimal: lambda v: format(v, ".2f"),
        }
    }


class CashflowHistoryParameters(BaseModel):
    """Query parameters for cashflow history endpoint."""

    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    currency: Optional[str] = None
    date_from: Date
    date_to: Date
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    source: Optional[str] = None
    period: TransactionSummaryPeriod = TransactionSummaryPeriod.MONTH

    @model_validator(mode="after")
    def validate_ranges(self) -> "CashflowHistoryParameters":
        if self.date_from > self.date_to:
            raise ValueError("'date_from' must be before or equal to 'date_to'")
        if (
            self.amount_min is not None
            and self.amount_max is not None
            and self.amount_min > self.amount_max
        ):
            raise ValueError("'amount_min' must be before or equal to 'amount_max'")
        return self


# -------------------------------------------------------------------------
# Balance reporting (read-only; never mutates ledger).
# Balances = projections; FX = presentation at read time.
# -------------------------------------------------------------------------

_decimal_json = {"json_encoders": {Decimal: lambda v: format(v, ".2f")}}


class BalanceResponse(BaseModel):
    """Total balance as of a date in user base currency."""

    as_of: Date
    currency: str
    balance: Decimal

    model_config = {"populate_by_name": True, **_decimal_json}


class AccountBalanceItem(BaseModel):
    """Balance for one account (native and converted)."""

    account_id: UUID4
    account_name: str
    currency: str
    balance_native: Decimal
    balance_converted: Decimal

    model_config = {"populate_by_name": True, **_decimal_json}


class BalanceAccountsResponse(BaseModel):
    """Balance per account as of a date plus total in base currency."""

    as_of: Date
    currency: str
    accounts: list[AccountBalanceItem]
    total: Decimal

    model_config = {"populate_by_name": True, **_decimal_json}


class BalanceHistoryPoint(BaseModel):
    """One point in balance history (for charts/lists)."""

    date: str  # YYYY-MM-DD
    balance: Decimal

    model_config = dict(_decimal_json)


class BalanceHistoryResponse(BaseModel):
    """Balance history for a date range and period."""

    currency: str
    period: str  # day | week | month
    points: list[BalanceHistoryPoint]

    model_config = dict(_decimal_json)
