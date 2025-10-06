from __future__ import annotations

from collections.abc import Callable
from datetime import date as Date
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, ClassVar, List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.entities.transaction import Transaction, TransactionSource, TransactionType
from app.schemas.category_schemas import CategoryResponseBase
from app.schemas.installment_schemas import InstallmentBase


class TransactionRelatedEntity(BaseModel):
    id: UUID
    name: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "json_encoders": {UUID: str},
    }


class TransactionBase(BaseModel):
    account: TransactionRelatedEntity
    category: CategoryResponseBase
    group: Optional[TransactionRelatedEntity] = None
    recurrent_transaction_id: Optional[UUID] = None
    transfer_id: Optional[UUID] = None
    type: str
    amount: Decimal
    currency: Optional[str] = None
    date: Date
    source: str = TransactionSource.MANUAL.value
    has_installments: bool = False
    installments: Optional[List[InstallmentBase]] = None

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: lambda value: format(value, ".2f")},
    }


class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TransferResponse(BaseModel):
    id: UUID
    from_account_id: UUID
    to_account_id: UUID
    transfer_id: UUID
    amount: Decimal
    currency: Optional[str] = None
    tag: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TransactionCreate(BaseModel):
    account_id: UUID
    category_id: UUID
    group_id: Optional[UUID] = None
    type: str
    amount: Decimal
    currency: Optional[str] = None
    date: Date
    source: str = TransactionSource.MANUAL.value
    has_installments: bool = False

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: lambda value: format(value, ".2f")},
    }

    @field_validator("date", mode="before")
    @classmethod
    def ensure_date(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.date()
        return value

    def to_model(self, current_user_id: UUID) -> Transaction:
        return Transaction(
            user_id=current_user_id,
            account_id=self.account_id,
            category_id=self.category_id,
            group_id=self.group_id,
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
    date: Optional[Date] = None
    source: Optional[str] = None
    has_installments: Optional[bool] = None

    model_config = {"from_attributes": True}

    @field_validator("date", mode="before")
    @classmethod
    def ensure_date(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.date()
        return value


class TransferTransactionCreate(BaseModel):
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal
    date: Date
    tag: Optional[UUID] = None

    model_config = {"from_attributes": True}

    def build_from_transaction(
        self, user_id: UUID, transfer_id: UUID, transfer_category: UUID
    ) -> Transaction:
        return Transaction(
            user_id=user_id,
            account_id=self.from_account_id,
            transfer_id=transfer_id,
            category_id=transfer_category,
            amount=self.amount,
            date=self.date,
            source=TransactionSource.MANUAL,
            type=TransactionType.EXPENSE,
        )

    def build_to_transaction(
        self, user_id: UUID, transfer_id: UUID, transfer_category: UUID
    ) -> Transaction:
        return Transaction(
            user_id=user_id,
            account_id=self.to_account_id,
            transfer_id=transfer_id,
            category_id=transfer_category,
            amount=self.amount,
            date=self.date,
            source=TransactionSource.MANUAL,
            type=TransactionType.INCOME,
        )


class TransactionSearch(BaseModel):
    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    type: Optional[str] = None
    currency: Optional[str] = None
    date_from: Optional[Date] = None
    date_to: Optional[Date] = None
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
