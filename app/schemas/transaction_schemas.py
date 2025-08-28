from datetime import date, datetime, timezone
from typing import Any, Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel

from app.entities.transaction import Transaction


class TransactionBase(BaseModel):
    account_id: UUID
    category_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    recurrent_transaction_id: Optional[UUID] = None
    transfer_id: Optional[UUID] = None
    type: str
    amount: Decimal
    currency: Optional[str] = None
    date: date
    source: str = "manual"
    has_installments: bool = False

    model_config = {"from_attributes": True}

    def to_model(self, current_user_id: UUID) -> Transaction:
        return Transaction(
            user_id=current_user_id,
            account_id=self.account_id,
            category_id=self.category_id,
            group_id=self.group_id,
            recurrent_transaction_id=self.recurrent_transaction_id,
            transfer_id=self.transfer_id,
            type=self.type,
            amount=self.amount,
            currency=self.currency,
            date=self.date,
            source=self.source,
            has_installments=self.has_installments,
            created_at=datetime.now(timezone.utc),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "category_id": self.category_id,
            "group_id": self.group_id,
            "recurrent_transaction_id": self.recurrent_transaction_id,
            "transfer_id": self.transfer_id,
            "type": self.type,
            "amount": self.amount,
            "currency": self.currency,
            "date": self.date,
            "source": self.source,
            "has_installments": self.has_installments,
            "created_at": datetime.now(timezone.utc),
        }


class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TransactionCreate(TransactionBase):
    def to_model(self, current_user_id: UUID) -> Transaction:
        return Transaction(
            user_id=current_user_id,
            account_id=self.account_id,
            category_id=self.category_id,
            group_id=self.group_id,
            recurrent_transaction_id=self.recurrent_transaction_id,
            transfer_id=self.transfer_id,
            type=self.type,
            amount=self.amount,
            currency=self.currency,
            date=self.date,
            source=self.source,
            has_installments=self.has_installments,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )


class TransactionUpdate(BaseModel):
    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    recurrent_transaction_id: Optional[UUID] = None
    transfer_id: Optional[UUID] = None
    type: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    date: Optional[date] = None
    source: Optional[str] = None
    has_installments: Optional[bool] = None

    model_config = {"from_attributes": True}


class TransactionSearch(BaseModel):
    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    type: Optional[str] = None
    currency: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    source: Optional[str] = None
    has_installments: Optional[bool] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "category_id": "123e4567-e89b-12d3-a456-426614174001",
                "type": "expense",
                "currency": "USD",
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
                "amount_min": "10.00",
                "amount_max": "1000.00",
                "source": "manual",
                "has_installments": False
            }
        }
    }