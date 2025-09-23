from collections.abc import Callable
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, ClassVar, Optional
from uuid import UUID

from pydantic import BaseModel

from app.entities.transaction import Transaction, TransactionSource, TransactionType


class TransactionBase(BaseModel):
    account_id: UUID
    category_id: UUID
    group_id: Optional[UUID] = None
    recurrent_transaction_id: Optional[UUID] = None
    transfer_id: Optional[UUID] = None
    type: TransactionType
    amount: Decimal
    currency: Optional[str] = None
    date: date
    source: TransactionSource = TransactionSource.MANUAL
    has_installments: bool = False

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: lambda value: format(value, ".2f")},
    }

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
            "account_id": str(self.account_id) if self.account_id else None,
            "category_id": str(self.category_id) if self.category_id else None,
            "group_id": str(self.group_id) if self.group_id else None,
            "recurrent_transaction_id": (
                str(self.recurrent_transaction_id)
                if self.recurrent_transaction_id
                else None
            ),
            "transfer_id": str(self.transfer_id) if self.transfer_id else None,
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


class TransferTransactionCreate(BaseModel):
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal
    date: date
    tag: Optional[UUID] = None

    model_config = {"from_attributes": True}

    def build_from_transaction(self, user_id: UUID, transfer_id: UUID) -> Transaction:
            return Transaction(
            user_id=user_id,
            account_id=self.from_account_id,
            transfer_id=transfer_id,
            amount=self.amount,
            date=self.date,
            source=TransactionSource.MANUAL,
            type=TransactionType.EXPENSE,
        )

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
                "has_installments": False,
            }
        },
    }

    _filter_builders: ClassVar[dict[str, Callable[[Any], Any]]] = {
        "account_id": lambda value: Transaction.account_id == value,
        "category_id": lambda value: Transaction.category_id == value,
        "group_id": lambda value: Transaction.group_id == value,
        "type": lambda value: Transaction.type == value,
        "currency": lambda value: Transaction.currency == value,
        "date_from": lambda value: Transaction.date >= value,
        "date_to": lambda value: Transaction.date <= value,
        "amount_min": lambda value: Transaction.amount >= value,
        "amount_max": lambda value: Transaction.amount <= value,
        "source": lambda value: Transaction.source == value,
        "has_installments": lambda value: Transaction.has_installments == value,
    }

    def build_filters(self) -> list[Any]:
        """Generate SQLAlchemy filter expressions for the provided search fields."""

        filters: list[Any] = []
        for field_name, value in self.model_dump(exclude_unset=True).items():
            if value is None:
                # Skip filters explicitly set to null to mimic previous behaviour
                continue

            builder = self._filter_builders.get(field_name)
            if builder:
                filters.append(builder(value))

        return filters
