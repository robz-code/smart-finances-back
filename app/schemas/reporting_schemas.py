from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import date as Date

from pydantic import UUID4, BaseModel, Field, model_validator

from app.entities.category import CategoryType
from app.entities.transaction import TransactionType


class TransactionSummaryPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


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
