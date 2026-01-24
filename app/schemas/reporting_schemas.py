from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import UUID4, BaseModel

from app.entities.category import CategoryType


class TransactionSummaryPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class CategorySummaryResponse(BaseModel):
    id: UUID4
    name: str
    type: CategoryType
    icon: Optional[str] = None
    color: Optional[str] = None
    transaction_amount: str  # Formatted decimal, e.g. "150.00"
