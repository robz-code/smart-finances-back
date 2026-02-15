from __future__ import annotations

from collections.abc import Callable
from datetime import date as Date
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, ClassVar, List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from app.entities.transaction import Transaction, TransactionSource, TransactionType
from app.schemas.category_schemas import CategoryResponseBase
from app.schemas.concept_schemas import ConceptTransactionCreate
from app.schemas.reporting_schemas import TransactionSummaryPeriod
from app.schemas.tag_schemas import TagTransactionCreate


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
    concept: Optional[TransactionRelatedEntity] = None
    tags: Optional[List[TransactionRelatedEntity]] = None
    transfer_id: Optional[UUID] = None
    type: str
    amount: Decimal
    currency: Optional[str] = None
    date: Date
    source: str = TransactionSource.MANUAL.value

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
    transfer_id: UUID
    from_transaction: TransactionResponse
    to_transaction: TransactionResponse


class TransactionCreate(BaseModel):
    account_id: UUID
    category_id: UUID
    concept: Optional[ConceptTransactionCreate] = None
    tags: Optional[List[TagTransactionCreate]] = None
    type: str
    amount: Decimal
    currency: Optional[str] = None
    date: Date
    source: str = TransactionSource.MANUAL.value

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
            type=self.type,
            amount=self.amount,
            currency=self.currency,
            date=self.date,
            source=self.source,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )


class TransactionUpdate(BaseModel):
    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    type: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    date: Optional[Date] = None
    source: Optional[str] = None

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
    concept: Optional[UUID] = None
    tags: Optional[List[UUID]] = None

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
    type: Optional[str] = None
    currency: Optional[str] = None
    date_from: Optional[Date] = None
    date_to: Optional[Date] = None
    period: Optional[TransactionSummaryPeriod] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    source: Optional[str] = None

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
            }
        },
    }

    _filter_builders: ClassVar[dict[str, Callable[[Any], Any]]] = {
        "account_id": lambda value: Transaction.account_id == value,
        "category_id": lambda value: Transaction.category_id == value,
        "type": lambda value: Transaction.type == value,
        "currency": lambda value: Transaction.currency == value,
        "date_from": lambda value: Transaction.date >= value,
        "date_to": lambda value: Transaction.date <= value,
        "amount_min": lambda value: Transaction.amount >= value,
        "amount_max": lambda value: Transaction.amount <= value,
        "source": lambda value: Transaction.source == value,
    }

    @model_validator(mode="after")
    def ensure_date_range_or_period(self) -> "TransactionSearch":
        """
        Enforce mutually exclusive date strategies:
        - Either `period` OR (`date_from` and `date_to`) OR neither.
        """
        if self.period is not None and (
            self.date_from is not None or self.date_to is not None
        ):
            raise ValueError("Use either 'period' or 'date_from'/'date_to', not both.")

        if (self.date_from is None) ^ (self.date_to is None):
            raise ValueError(
                "Both 'date_from' and 'date_to' must be provided together."
            )

        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("'date_from' must be before or equal to 'date_to'.")

        return self

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


class RecentTransactionsParams(BaseModel):
    """
    Query params for recent transactions endpoint.
    Only `limit` is allowed. Date-related params are explicitly rejected.
    """

    limit: Optional[int] = None
    date_from: Optional[Date] = None
    date_to: Optional[Date] = None
    period: Optional[TransactionSummaryPeriod] = None

    @model_validator(mode="after")
    def validate_recent_params(self) -> "RecentTransactionsParams":
        if self.limit is None:
            raise ValueError("limit is required.")

        if self.limit not in {5, 10, 20, 50, 100}:
            raise ValueError("limit must be one of: 5, 10, 20, 50, 100.")

        if (
            self.date_from is not None
            or self.date_to is not None
            or self.period is not None
        ):
            raise ValueError(
                "Recent transactions does not support date filters or period."
            )

        return self


class RecentTransactionsResponse(BaseModel):
    results: List[TransactionResponse]
