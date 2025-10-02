from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from app.entities.account import Account, AccountType


class AccountBase(BaseModel):
    name: str
    type: AccountType
    currency: Optional[str] = None
    initial_balance: Optional[float] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True

    def to_model(self, current_user_id: UUID) -> Account:
        return Account(
            user_id=current_user_id,
            name=self.name,
            type=self.type.value,
            currency=self.currency,
            initial_balance=self.initial_balance,
            color=self.color,
            created_at=datetime.now(timezone.utc),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "currency": self.currency,
            "initial_balance": self.initial_balance,
            "color": self.color,
            "created_at": datetime.now(timezone.utc),
        }


class AccountResponse(AccountBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AccountCreate(AccountBase):

    def to_model(self, current_user_id: UUID) -> Account:
        return Account(
            user_id=current_user_id,
            name=self.name,
            type=self.type.value,
            currency=self.currency,
            initial_balance=self.initial_balance,
            color=self.color,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[AccountType] = None
    currency: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True
