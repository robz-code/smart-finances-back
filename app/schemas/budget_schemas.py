from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.entities.budget import Budget


class BudgetBase(BaseModel):
    name: str
    recurrence: str
    amount: Decimal
    account_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True

    def to_model(self, current_user_id: UUID) -> Budget:
        return Budget(
            user_id=current_user_id,
            account_id=self.account_id,
            name=self.name,
            recurrence=self.recurrence,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=self.amount,
            created_at=datetime.now(timezone.utc),
        )


class BudgetResponse(BudgetBase):
    id: UUID
    user_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BudgetCreate(BudgetBase):

    def to_model(self, current_user_id: UUID) -> Budget:
        return Budget(
            user_id=current_user_id,
            account_id=self.account_id,
            name=self.name,
            recurrence=self.recurrence,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=self.amount,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )


class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    recurrence: Optional[str] = None
    amount: Optional[Decimal] = None
    account_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True
