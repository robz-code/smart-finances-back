from pydantic import BaseModel
from typing import Optional
from datetime import datetime, UTC
from app.entities.account import Account, AccountType
from uuid import UUID


class AccountBase(BaseModel):
    
    name: str
    type: AccountType
    currency: Optional[str] = None
    initial_balance: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    def to_model(self, current_user_id: UUID):
        return Account(
            user_id=current_user_id,
            name=self.name,
            type=self.type.value,
            currency=self.currency,
            initial_balance=self.initial_balance,
            created_at=datetime.now(UTC),
        )

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type.value,
            "currency": self.currency,
            "initial_balance": self.initial_balance,
            "created_at": datetime.now(UTC),
        }

class AccountCreate(AccountBase):
    pass