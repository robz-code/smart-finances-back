from datetime import date as Date
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class InstallmentBase(BaseModel):
    id: UUID
    due_date: Date
    amount: Decimal
    installment_number: int

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: lambda value: format(value, ".2f")},
    }

    def to_model(self) -> dict[str, Any]:
        return {
            "due_date": self.due_date,
            "amount": self.amount,
        }


class InstallmentCreate(BaseModel):
    due_date: Date
    amount: Decimal

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: lambda value: format(value, ".2f")},
    }

    @field_validator("due_date", mode="before")
    @classmethod
    def ensure_date(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.date()
        return value


class InstallmentUpdate(BaseModel):
    due_date: Optional[Date] = None
    amount: Optional[Decimal] = None

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: lambda value: format(value, ".2f")},
    }

    @field_validator("due_date", mode="before")
    @classmethod
    def ensure_date(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.date()
        return value
