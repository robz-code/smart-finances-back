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
